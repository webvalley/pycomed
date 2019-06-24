import SimpleITK as sitk
import numpy as np

import dicom_utils as du

# When the scan direction is bigger than this threshold
# we assume that is in axial orientation.
AXIAL_ORIENTATION_THRESHOLD = 0.9
NO_INDEX = -1


class Scan:
    """

    Class representing the scan with all the meta-data
    needed for the whole algorithm to work.

    """

    def __init__(self, scan, path, depth, direction):
        """

        Initialization method of the object.
        Args:
            scan: scan file loaded from memory.
            path: path of the scan.
            depth: depth of the scan, that is equals to the lowest
                    dimension of the scan.
            direction: direction of the scan, needed to detect its orientation

        """

        self.scan = scan
        self.path = path
        self.depth = depth
        self.direction = direction


#
def read_scans_and_find_ref_scan(sequences_paths):
    """

    Finds the index of the reference scan, which is the scan with
    the deepest depth from the batch. This function also returns
    an array with all the scans inside of the specific folder.

    Args:
        sequences_paths: paths of the sequences we want to read and
                            extract meta-data from.

    Returns: an array of scans and the index of the reference scan image.

    """

    # Reads all the DICOM sequences and the needed metadata.
    scans = get_scans_and_metadata(sequences_paths)
    # Find the reference scan index inside of the scans array.
    ref_scan_index = find_ref_scan_index(scans)
    # Resamples the reference image and updates the scans array.
    ref_scan = resample_ref_scan(scans[ref_scan_index])
    scans[ref_scan_index] = ref_scan

    return scans, ref_scan_index


def get_scans_and_metadata(sequences_paths):
    """

    Iterates over all sequences and reads the scans with their meta-data.

    Args:
        sequences_paths: paths of the sequences we want to read and
                            extract meta-data from.

    Returns: an array of scans with the meta-data.

    """

    # Scans
    scans = []

    for sequences_path in sequences_paths:
        loaded_scan = du.load_series(sequences_path)
        if loaded_scan is not None:
            scan = sitk.Cast(loaded_scan, sitk.sitkFloat32)
            scan_path = sequences_path
            scan_depth = np.min(loaded_scan.GetSize())
            scan_direction = np.diag(np.array(loaded_scan.GetDirection()).reshape((3, 3)))
            scans.append(Scan(scan, scan_path, scan_depth, scan_direction))

    return scans


def find_ref_scan_index(scans):
    """

    Searches for the reference scan in the scans array, we will look
    for the scan with an axial orientation and with the highest depth.

    Args:
        scans: array of all scans we read from a specific directory.

    Returns: the index of the reference scan related to the scans array we passed.

    """

    ref_scan_index = 0
    current_max_depth_scan_value = 0

    for i, scan in enumerate(scans):
        # We are going to choose the scans that are with an axial view and the depth is the highest.
        if (all(direction > AXIAL_ORIENTATION_THRESHOLD for direction in scan.direction)) \
                & scan.depth > current_max_depth_scan_value:
            ref_scan_index = i
            current_max_depth_scan_value = scan.depth

    return ref_scan_index


# Applies resampling on the scan with a spacing of 1,1,1.
def resample_ref_scan(ref_scan):
    """

    Performs a resampling of the reference image using a spacing of 1mm.

    Args:
        ref_scan: reference scan.

    Returns: the resampled scan.
    """

    ref_scan.scan = sitk.Cast(du.processing.resample(ref_scan.scan, spacing=(1., 1., 1.)), sitk.sitkFloat32)
    return ref_scan


def perform_registration(moving_image, fixed_image):
    """
    Performs the registration on the two images.

    Args:
        moving_image: image that we want to register.
        fixed_image: image that we want to align on.

    Returns: the registered scan.

    """

    registration_method = create_registration_method(moving_image, fixed_image)

    registration_transform = registration_method.Execute(fixed_image, moving_image)

    return sitk.Resample(moving_image, fixed_image, registration_transform)


def create_registration_method(moving_image, fixed_image):
    """

    Initializes and sets all the method necessary for the registration to
    work. The parameters are custom tuned by hand but in future there will
    be an option through the UI that will enable the user to toggle this parameters
    to achieve the best results.

    Args:
        moving_image: image that we want to register.
        fixed_image: image that we want to align on.

    Returns:

    """

    registration_method = sitk.ImageRegistrationMethod()

    # Registration parameters.
    registration_method.SetMetricAsMattesMutualInformation(numberOfHistogramBins=50)
    registration_method.SetMetricSamplingStrategy(registration_method.RANDOM)
    registration_method.SetMetricSamplingPercentage(0.01)
    registration_method.SetInterpolator(sitk.sitkBSpline)
    registration_method.SetOptimizerAsGradientDescent(learningRate=1, numberOfIterations=100)
    registration_method.SetOptimizerScalesFromPhysicalShift()
    registration_method.SetShrinkFactorsPerLevel(shrinkFactors=[4, 2, 1])
    registration_method.SetSmoothingSigmasPerLevel(smoothingSigmas=[2, 1, 0])
    registration_method.SmoothingSigmasAreSpecifiedInPhysicalUnitsOn()
    registration_method.SetInitialTransform(create_initial_transform(moving_image, fixed_image), inPlace=False)

    return registration_method


def create_initial_transform(moving_image, fixed_image):
    """

    Creates a specific transformation needed for the registration
    to work properly.

    Args:
        moving_image: image that we want to register.
        fixed_image: image that we want to align on.

    Returns: the initial transform instance.

    """

    return sitk.CenteredTransformInitializer(fixed_image, moving_image, sitk.Euler3DTransform(),
                                             sitk.CenteredTransformInitializerFilter.GEOMETRY)

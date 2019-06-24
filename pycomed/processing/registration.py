import os
import numpy as np
import SimpleITK as sitk

from pycomed.entities import SITKScan

# When the scan direction is bigger than this threshold
# we assume that is in axial orientation.
AXIAL_ORIENTATION_THRESHOLD = 0.9
NO_INDEX = -1


class SITKHelper:
    """Class containing helper methods to use the SimpleITK library.

    """

    @staticmethod
    def load_series(scan_path, metadata=False):
        """Loads a series of DICOM slices from the folder of the scan.
        In the case of DICOM files the scan_path is the folder in which all the sequences of
        that scan are saved.

        Returns: the SimpleITK scan scan or both the scan and its
                metadata.

        """
        reader = sitk.ImageSeriesReader()
        reader.LoadPrivateTagsOn()
        dicom_names = reader.GetGDCMSeriesFileNames(scan_path)
        reader.SetFileNames(dicom_names)

        try:
            scan = reader.Execute()

            if metadata:
                files = os.listdir(scan_path)
                file_metadata = os.path.join(scan_path, files[0])
                reader = sitk.ImageFileReader()
                reader.LoadPrivateTagsOn()
                reader.SetFileName(file_metadata)

                scan_w_metadata = reader.Execute()

                return scan, scan_w_metadata
            else:
                return scan
        except RuntimeError:
            print(f"An error occurred while reading the dicom file in {scan_path}.")
            return None

    @staticmethod
    def write_scan_as_nifti(scan, path):
        """Writes a scan on the disk in a specific path.

        Args:
            scan: scan object read by SimpleITK.
            path: path where the scan will be written.

        """

        sitk.WriteImage(scan, path)

    @staticmethod
    def get_fixed_scan(scans):
        """Finds the index of the reference scan, which is the scan with
        the deepest depth from the batch. This function also returns
        an array with all the scans inside of the specific folder.

        Args:
            scans: scans read by the reader.

        Returns: the fixed scan object as a SITKScan.

        """

        # Reads all the DICOM sequences with their related metadata.
        scans = SITKHelper.read_scans(scans)
        # Find the fixed scan index inside of the scans array.
        fixed_scan_index = SITKHelper.get_fixed_scan_index(scans)
        # Resamples the reference image and updates the scans array.
        scans[fixed_scan_index].scan = sitk.Cast(
            SITKHelper.resample(scans[fixed_scan_index].scan, spacing=(1., 1., 1.)), sitk.sitkFloat32)

        return scans[fixed_scan_index]

    @staticmethod
    def read_scans(scans):
        """Iterates over all sequences and reads the scans with their meta-data.

        Args:
            scans: scans read by the reader.

        Returns: an array of scans with the meta-data.

        """

        sitk_scans = []

        for scan in scans:
            loaded_scan = SITKHelper.load_series(scan.path)
            if loaded_scan is not None:
                loaded_scan = sitk.Cast(loaded_scan, sitk.sitkFloat32)

                scan_path = scan.path
                scan_depth = np.min(loaded_scan.GetSize())
                scan_direction = np.diag(np.array(loaded_scan.GetDirection()).reshape((3, 3)))

                sitk_scans.append(SITKScan(scan_path, loaded_scan, scan_depth, scan_direction))

        return sitk_scans

    @staticmethod
    def get_fixed_scan_index(scans):
        """Searches for the reference scan in the scans array, we will look
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

    @staticmethod
    def resample(scan, spacing=None, size=None, interpolator=sitk.sitkBSpline):
        """Resamples a SimpleITK scan with a specific shaping and size.


        Args:
            scan: scan read by SimpleITK.
            spacing: spacing between the voxels.
            size: size of the scan.
            interpolator: interpolator used for the resampling.

        Returns: the resampled scan.

        """
        assert spacing is not None or size is not None, "Either pixel_size or pixel_number should be defined, not both"
        assert not (
                spacing is not None and size is not None), "Either pixel_size or pixel_number should be defined, not both"

        spacing_orig = scan.GetSpacing()
        size_orig = scan.GetSize()

        dimX = spacing_orig[0] * size_orig[0]
        dimY = spacing_orig[1] * size_orig[1]
        dimZ = spacing_orig[2] * size_orig[2]

        if spacing is not None:
            sizeX = int(dimX / spacing[0])
            sizeY = int(dimY / spacing[1])
            sizeZ = int(dimZ / spacing[2])

            size = (sizeX, sizeY, sizeZ)

        elif size is not None:
            spaceX = dimX / size[0]  # Musk
            spaceY = dimY / size[1]
            spaceZ = dimZ / size[2]

            spacing = (spaceX, spaceY, spaceZ)

        target = sitk.Image(size, sitk.sitkFloat32)
        target.SetSpacing(spacing)
        target.SetOrigin(scan.GetOrigin())

        out = sitk.Resample(scan, target)

        return out


class SITKRegistrationHelper(SITKHelper):
    """Class containing helper methods to perform registration with the SimpleITK library.
    See Also: https://simpleitk.readthedocs.io/en/master/Documentation/docs/source/registrationOverview.html

    """

    @staticmethod
    def perform_registration(moving_scan, fixed_scan):
        """Performs the registration on the two scans.

        Args:
            moving_scan: scan that we want to register.
            fixed_scan: scan that we want to align on.

        Returns: the registered scan.

        """

        registration_method = SITKRegistrationHelper.create_registration_method(moving_scan, fixed_scan)

        registration_transform = registration_method.Execute(fixed_scan, moving_scan)

        return sitk.Resample(moving_scan, fixed_scan, registration_transform)

    @staticmethod
    def create_registration_method(moving_scan, fixed_scan):
        """Initializes and sets all the method necessary for the registration to
        work. The parameters are custom tuned by hand but in future there will
        be an option through the UI that will enable the user to toggle this parameters
        to achieve the best results.

        Args:
            moving_scan: scan that we want to register.
            fixed_scan: scan that we want to align on.

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
        registration_method.SetInitialTransform(
            SITKRegistrationHelper.create_initial_transform(moving_scan, fixed_scan), inPlace=False)

        return registration_method

    @staticmethod
    def create_initial_transform(moving_scan, fixed_scan):
        """Creates a specific transformation needed for the registration
        to work properly.

        Args:
            moving_scan: scan that we want to register.
            fixed_scan: scan that we want to align on.

        Returns: the initial transform instance.

        """

        return sitk.CenteredTransformInitializer(fixed_scan, moving_scan, sitk.Euler3DTransform(),
                                                 sitk.CenteredTransformInitializerFilter.GEOMETRY)

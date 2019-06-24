import os
from abc import ABC, abstractmethod
from enum import Enum

import SimpleITK as sitk

import pycomed


class MRIImage(ABC):
    """Base class that describes the behavior that any MRI image
    needs to inherit.

    """

    @abstractmethod
    def perform_registration(self, fixed_image, output_path):
        """Performs the registration using as the moving image the object that
        implements this method and registers it on a fixed image given as param.

        Registration is treated as an optimization problem with the goal of finding the spatial mapping
        that will bring the moving image into alignment with the fixed image.

        Args:
            fixed_image: fixed image that will be used to register.
            output_path: path in which the registered image will be saved as nifti.

        Returns: the output path of the registered image so the user can choose how to read it.

        """

        pass


class Scan:
    """Base scan class representing the scan entity.

    """

    def __init__(self, path):
        self.path = path


class DICOMScan(Scan, MRIImage):
    """DICOM scan entity. Depeding on the library used to read DICOM files,
    the scan_image could be an object or an array of objects.

    """

    def __init__(self, path, sequences=None):
        super(DICOMScan, self).__init__(path)
        self.sequences = sequences

    def add_sequence(self, sequence):
        if self.sequences is None:
            self.sequences = []

        self.sequences.append(sequence)

    def perform_registration(self, fixed_image, output_path):
        """InheritDoc.

        """

        sitk_moving_image = sitk.Cast(pycomed.SITKHelper.load_series(self.path), sitk.sitkFloat32)
        sitk_fixed_image = sitk.Cast(pycomed.SITKHelper.load_series(fixed_image.path), sitk.sitkFloat32)

        registered_scan = pycomed.SITKRegistrationHelper.perform_registration(sitk_moving_image, sitk_fixed_image)

        if not os.path.exists(output_path):
            os.makedirs(output_path)

        patient_name = self.sequences[0].PatientName
        moving_image_series_number = self.sequences[0].SeriesNumber
        fixed_image_series_number = fixed_image.sequences[0].SeriesNumber
        file_name = f'{patient_name}_SEQ{moving_image_series_number}->SEQ{fixed_image_series_number}.nii'

        # We will write the registered image as a nifti file.
        pycomed.SITKHelper.write_scan_as_nifti(registered_scan, os.path.join(output_path, file_name))

        return output_path


class SITKScan(Scan):
    """SITKScan used by the registration algorithm.

    """

    def __init__(self, path, scan, depth, direction):
        """

        Initialization method of the object.
        Args:
            scan: scan file loaded from memory.
            path: path of the scan.
            depth: depth of the scan, that is equals to the lowest
                    dimension of the scan.
            direction: direction of the scan, needed to detect its orientation

        """
        super(SITKScan, self).__init__(path)
        self.scan = scan
        self.depth = depth
        self.direction = direction


class ScanType(Enum):
    """Enum that specifies all the scan types that are supported by
    the pycomed SDK.

    """

    DICOM = 0

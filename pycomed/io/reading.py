"""This module contains all the classes used to read the organized dataset. It provides
helper methods to query data in an efficient and easy way.

"""

import datetime
import logging
import os
import sys
from abc import ABC, abstractmethod

import pydicom
from pydicom.errors import InvalidDicomError

from pycomed.entities import DICOMScan, ScanType
from pycomed.exceptions import MalformedDatasetException, WrongDateIntervalException, ScanTypeNotSupportedException
from pycomed.processing import SITKHelper

# Setting up the logger.
logger = logging.getLogger("pycomed reading.py logger")
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


class DatasetValidator:
    """Checks if the dataset given in input has the correct schema or not.

    """

    def __init__(self, dataset_path):
        self.dataset_path = dataset_path

    def validate(self, scan_type=None):
        """Validates a dataset that follows a specific schema.

        Args:
            scan_type: type of the scan that needs to be validated

        """

        # Checking if the first layer contains all folders, that in our case
        # corresponds to the patients.
        if self.are_all_folders(self.dataset_path):
            for patient_folder_name in os.listdir(self.dataset_path):
                patient_path = os.path.join(self.dataset_path, patient_folder_name)

                # Checking if the second layer contains all folders, that in our case
                # corresponds to the scans folders containing all the DICOM scans.
                if self.are_all_folders(patient_path):
                    for scan_folder_name in os.listdir(patient_path):
                        scan_path = os.path.join(patient_path, scan_folder_name)

                        # Checking if the third layer contains all files that can be in whatever extension we want.
                        if not self.are_all_files(scan_path, scan_type):
                            raise MalformedDatasetException()
                else:
                    raise MalformedDatasetException()

        else:
            raise MalformedDatasetException()

    def are_all_folders(self, path):
        """Checks if inside of a specific path there are only folders.

        Args:
            path: path in which to look for folders.

        Returns: true if there are only folders, false otherwise.

        """

        if not os.path.exists(path):
            return False

        return len(list(filter(lambda content_name: os.path.isdir(os.path.join(path, content_name)),
                               os.listdir(path)))) == len(os.listdir(path)) and not len(os.listdir(path)) == 0

    def are_all_files(self, path, scan_type=None):
        """Checks if inside of a specific path there are only files.

        Args:
            path: path in which to look for folders.
            scan_type: type of the scan that needs to be validated
            because we can also have any extension.

        Returns: true if there are only files, false otherwise.

        """

        if not os.path.exists(path):
            return False

        return len(list(filter(
            lambda file_name: not os.path.isdir(
                os.path.join(path, file_name) and self.check_scan_type(os.path.join(path, file_name), scan_type)),
            os.listdir(path)))) == len(os.listdir(path)) and not len(os.listdir(path)) == 0

    def check_scan_type(self, file_path, scan_type):
        """Checks if the file has the correct file format.

        Args:
            file_path: path of the file to check the scan of.
            scan_type: type of the scan that we want.

        Returns: true if the scan type is correct, false otherwise.

        """

        if scan_type == ScanType.DICOM:
            try:
                pydicom.dcmread(file_path, force=True)
                return True
            except InvalidDicomError:
                return False
        else:
            raise ScanTypeNotSupportedException()


class DatasetReader(ABC):
    """Base class that describes the basic behavior of the dataset reader.

    """

    def __init__(self, dataset_path):
        self._dataset_path = dataset_path

    @property
    def dataset_path(self):
        return self._dataset_path

    @abstractmethod
    def get_scans(self, filter_by=None):
        """Gets all the scans from the dataset that satisfy a filter function if supplied.

        Args:
            filter_by: function that filters the scans with a condition.

        Returns: a list of serialized scans.

        """

        pass

    @abstractmethod
    def get_scans_by_patient_name(self, patient_name):
        """Gets all the scans that have a specific patient name.

        Args:
            patient_name: name of the patient.

        Returns: a list of serialized scans.

        """

        pass

    @abstractmethod
    def get_scans_by_acquisition_date(self, from_date, to_date):
        """Gets all the scans that have been captured between a date interval.

        Args:
            from_date: from date.
            to_date: to date.

        Returns: a list of serialized scans.

        """

        pass

    @abstractmethod
    def get_scans_by_size(self, width, height, depth):
        """Gets all the scans that have a specific size.

        Args:
            width: width of the scan.
            height: height of the scan.
            depth: depth of the scan.

        Returns: a list of serialized scans.

        """

        pass

    @abstractmethod
    def get_fixed_image(self, patient_name):
        """Gets the fixed image of a specific patient. This method is useful
        if you want to perform registration without knowing which image to register on.

        Args:
            patient_name: name of the patient for which we want to find the fixed scan.

        Returns: the fixed serialized scan.


        """

        pass


class DICOMDatasetReader(DatasetReader):
    """Reads a specific dataset containing DICOM medical images after being
    organized.

    """

    def __init__(self, dataset_organizer):
        super(DICOMDatasetReader, self).__init__(dataset_path=dataset_organizer.organize())

    def get_scans(self, filter_by=None):
        """InheritDoc.

        """

        # List containing all the serialized scans.
        scans = []

        for patient_folder_name in os.listdir(self.dataset_path):
            patient_path = os.path.join(self.dataset_path, patient_folder_name)

            for scan_folder_name in os.listdir(patient_path):
                scan_path = os.path.join(patient_path, scan_folder_name)

                # Checking if the user has specified the condition.
                if filter_by:
                    if filter_by(scan_path):
                        scans.append(DICOMDatasetReaderHelper.serialize_scan(scan_path))
                else:
                    scans.append(DICOMDatasetReaderHelper.serialize_scan(scan_path))

        return scans

    def get_scans_by_patient_name(self, patient_name):
        """InheritDoc.

        """

        # List containing all the serialized scans.
        scans = []

        for patient_folder_name in os.listdir(self.dataset_path):
            patient_path = os.path.join(self.dataset_path, patient_folder_name)

            # If the folder name is equals to the patient name we will add all the scans inside.
            # This is done because we know for sure that all scans inside of that directory are from the patient
            # name written in the top folder. NB: in order for this to work you need the dataset formatted in the
            # correct way.
            if patient_folder_name == patient_name:
                for scan_folder_name in os.listdir(patient_path):
                    scans.append(DICOMDatasetReaderHelper.serialize_scan(os.path.join(patient_path, scan_folder_name)))

        return scans

    def get_scans_by_acquisition_date(self, from_date, to_date):
        """InheritDoc.

        """

        # If the date interval is not coherent we cannot query the dataset.
        if from_date > to_date:
            raise WrongDateIntervalException()

        return self.get_scans(lambda scan_path: DICOMDatasetReaderHelper.get_scan_acquisition_date(
            scan_path) >= from_date and DICOMDatasetReaderHelper.get_scan_acquisition_date(scan_path) <= to_date)

    def get_scans_by_size(self, width, height, depth):
        """InheritDoc.

        """
        return self.get_scans(
            lambda scan_path: DICOMDatasetReaderHelper.is_size_matching(scan_path, int(width), int(height), int(depth)))

    def get_fixed_image(self, patient_name):
        """InheritDoc.

        """

        patient_scans = self.get_scans_by_patient_name(patient_name)

        sitk_fixed_scan = SITKHelper.get_fixed_scan(patient_scans)

        return list(filter(lambda patient_scan: patient_scan.path == sitk_fixed_scan.path, patient_scans))[0]


class DICOMDatasetReaderHelper:
    """Helper class containing useful methods for reading DICOM files with pydicom.

    """

    @staticmethod
    def is_size_matching(scan_path, width, height, depth):
        """Checks if the size wanted by the user is the same as the size of the actual DICOM scan.

        Args:
            scan_path: path of the folder containing all the DICOM sequences of a specific scan.
            width: target width specified by the user.
            height: target height specified by the user.
            depth: target depth specified by the user.

        Returns: true if the size is matching, false otherwise.

        """

        scan_w, scan_h, scan_d = DICOMDatasetReaderHelper.get_scan_dimensions(scan_path)

        return scan_w == width and scan_h == height and scan_d == depth

    @staticmethod
    def get_scan_dimensions(scan_path):
        """Gets the three dimensions of the scan from the DICOM file.

        Args:
            scan_path: path of the folder containing all the DICOM sequences of a specific scan.

        Returns: a tuple containing the width, height and depth of the scan.

        """

        for scan_file_name in os.listdir(scan_path):
            scan = pydicom.dcmread(os.path.join(scan_path, scan_file_name))

            return scan.Columns, scan.Rows, len(os.listdir(scan_path))

    @staticmethod
    def get_scan_acquisition_date(scan_path):
        """Gets the scan acquisition date from the first DICOM file of the sequence
        and formats it into the datetime format.

        Args:
            scan_path: path of the folder containing all the DICOM sequences of a specific scan.

        Returns: the acquisition date in datetime format.

        """

        for scan_file_name in os.listdir(scan_path):
            return DICOMDatasetReaderHelper.parse_date(
                pydicom.dcmread(os.path.join(scan_path, scan_file_name)).AcquisitionDate)

    @staticmethod
    def serialize_scans(scans_paths):
        """Converts a list of scans folder containg DICOM files to DICOMScan objects
        that are easily usable in python.

        Args:
            scans_paths: list containg all the paths of the scans folders.

        Returns: a list of DICOMScan object representing a specific DICOM file.

        """

        # List containing all the serialized objects.
        scans = []

        # Loops for every scan path.
        for scan_path in scans_paths:
            # Appends the serialized scan object to the list of scans.
            scans.append(DICOMDatasetReaderHelper.serialize_scan(scan_path))

        return scans

    @staticmethod
    def serialize_scan(scan_path):
        """Converts a folder containing DICOM files to a DICOMScan object.

        Args:
            scan_path: path of the scan folder.

        Returns: a DICOMScan object representing a specific DICOM file with multiple layers.

        """

        # Initiates the scan object with his specific path.
        scan = DICOMScan(scan_path)

        # Loops for every DICOM file of the specific scan.
        for scan_file_name in os.listdir(scan_path):
            # Adds the DICOM file to the list of DICOM files of the DICOMScan object.
            sequence_path = os.path.join(scan_path, scan_file_name)
            scan.add_sequence(pydicom.dcmread(sequence_path))

        return scan

    @staticmethod
    def parse_date(date):
        """Converts the date from string to datetime format.

        """

        return datetime.datetime.strptime(date, "%Y%m%d")

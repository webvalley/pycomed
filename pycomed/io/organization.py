"""This module contains all the classes used to organize the dataset with a specific schema:
/rootDir: (contains n number of different patients)
    /patientX: (contains n number of different folders containing all the dicom files)
        /scanX: (folder containing the organized dicom files)

"""

import logging
import os
import shutil
import sys
from abc import ABC, abstractmethod

import pydicom
from pydicom.errors import InvalidDicomError

from pycomed.entities import ScanType
from pycomed.exceptions import MalformedDatasetException
from pycomed.io.reading import DatasetValidator

# Hidden files and folders start with a dot in any OS.
HIDDEN_FILE_REGEX = "."

# Setting up the logger.
logger = logging.getLogger("pycomed organization.py logger")
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


class DatasetOrganizer(ABC):
    """Base class that describes the basic behavior of the dataset organizer.

    """

    def __init__(self, input_path, output_path):
        self._input_path = input_path
        self._output_path = output_path

    @property
    def input_path(self):
        return self._input_path

    @property
    def output_path(self):
        return self._output_path

    @abstractmethod
    def organize(self):
        """Organizes all the medical images following the schema described above.

        Returns: the root path of the organized dataset.

        """

        pass


class DICOMDatasetOrganizer(DatasetOrganizer):
    """Organizes a specific dataset containing DICOM medical images.

    """

    def validate_dataset(self, dataset_path):
        """Checks if the dataset_path is already in the correct schema.

        Args:
            dataset_path: path of the dataset we want to check the schema of.

        Returns: true if the validation happens successfully, false otherwise.

        """

        try:
            DatasetValidator(dataset_path).validate(ScanType.DICOM)
            return True
        except MalformedDatasetException:
            return False

    def organize(self):
        """Moves the DICOM files from an unordered dataset to a ordered one. Using the patient name and
        series number as sorting criterias. In our case the output schema is specified at the top of this file.
        The algorithm works only with the following dataset schema:
        /rootDir: (contains n number of different patients)
            /patientX: (patient folder containing all the DICOM files of that patient, not organized)

        """

        # We will check if the dataset we want to organize is already organized.
        # If yes we will return the path of the organized dataset which will be the path
        # just validated.
        if self.validate_dataset(self.input_path):
            logger.debug("Dataset already valid, skipping organization.")
            return self.input_path
        elif self.validate_dataset(self.output_path):
            logger.debug("Dataset already valid, skipping organization.")
            return self.output_path

        logger.debug("Dataset is not valid, performing organization.")

        for root, dirs, files in os.walk(self.input_path):
            for scan_file_name in filter(lambda file_name: not file_name.startswith("."), files):
                input_scan_path = os.path.join(root, scan_file_name)

                try:
                    # Reading DICOM file.
                    dicom_file = pydicom.dcmread(input_scan_path)
                except InvalidDicomError:
                    logger.debug(f"Cannot read DICOM file at {input_scan_path}, skipping it.")
                    continue
                else:
                    # Reading DICOM metadata.
                    patient_name = dicom_file.PatientName
                    series_number = dicom_file.SeriesNumber

                    # Creating the output path for the specific patient.
                    output_scan_path = os.path.join(self.output_path, str(patient_name), str(series_number))

                    # Creating the output directory if is not already existing.
                    os.makedirs(output_scan_path, exist_ok=True)
                    # We are going to copy the DICOM file from the input path into the output path.
                    shutil.copyfile(input_scan_path, f"{output_scan_path}/{scan_file_name}")

        return self.output_path

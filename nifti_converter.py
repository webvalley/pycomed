import os
import SimpleITK as sitk
import matplotlib.pyplot as plt
import dicom_utils as du
import logging
import sys

logger = logging.getLogger("Registration logger")
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

MOVING_SCAN_TYPE = "M"
FIXED_SCAN_TYPE = "F"

INPUT_PATH = f'/Volumes/SamsungT5/OPBG_Data/by_type/MB_by_sequence'
OUTPUT_PATH = f'/Volumes/SamsungT5/OPBG_Data/by_type/MB_by_sequence_nii'

# Loops over patients.
for patient_code in filter(lambda path: not path.startswith('.'), os.listdir(INPUT_PATH)):
    patient_path = os.path.join(INPUT_PATH, patient_code)

    # Preparing the array that will contain all the paths of the scans.
    patient_scans_paths = []
    patient_scans_numbers = []

    # Creating an output folder for each patient.
    output_patient_path = os.path.join(OUTPUT_PATH, patient_code)
    os.makedirs(output_patient_path, exist_ok=True)

    # Loops over the scans of the patient.
    for patient_scan_number in os.listdir(patient_path):
        patient_scans_paths.append(os.path.join(patient_path, patient_scan_number))
        patient_scans_numbers.append(patient_scan_number)

    # Finds the reference image inside of the patient folder and
    # returns an array with all the scans.
    scans, ref_scan_index = du.read_scans_and_find_ref_scan(patient_scans_paths)

    print("----------")

    # Looping on all scans and converting them to nifti.
    for (i, scan_obj) in enumerate(scans):
        logger.debug(f"Writing image from {patient_scans_paths[i]}")
        scan_type = MOVING_SCAN_TYPE

        if i == ref_scan_index:
            scan_type = FIXED_SCAN_TYPE
            logger.debug(f"Reference scan found at {scan_obj.path}")

        sitk.WriteImage(scan_obj.scan, os.path.join(output_patient_path, f"{scan_type}_{patient_scans_numbers[i]}.nii.gz"))





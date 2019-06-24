import os
import shutil

import pydicom

BASE_PATH = '/Volumes/SamsungT5/OPBG_Data/by_type'
INPUT_DIR = f'{BASE_PATH}/MB'
OUTPUT_DIR = f'{BASE_PATH}/MB_by_sequence'

patients = os.listdir(INPUT_DIR)

for patient in patients:
    os.makedirs(f'{OUTPUT_DIR}/{patient}', exist_ok=True)

    print("Patient " + patient)
    if not patient.startswith("."):
        patient_files = os.listdir(f'{INPUT_DIR}/{patient}')

        for dicom_file in patient_files:
            print("Dicom file " + dicom_file)
            filePath = f'{INPUT_DIR}/{patient}/{dicom_file}'

            if not os.path.isdir(filePath) and not dicom_file.startswith("."):
                print(f"Reading dicom at: {filePath}")
                dicom = pydicom.dcmread(filePath, force=True)
                number = dicom.SeriesNumber
                os.makedirs(f'{OUTPUT_DIR}/{patient}/{number}', exist_ok=True)
                shutil.copyfile(f'{INPUT_DIR}/{patient}/{dicom_file}', f'{OUTPUT_DIR}/{patient}/{number}/{dicom_file}')

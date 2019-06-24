import os
import SimpleITK as sitk
import matplotlib.pyplot as plt
import dicom_utils as du
import logging
import sys
from collections import defaultdict

logger = logging.getLogger("Registration logger")
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


def print_image(image):
    np = sitk.GetArrayFromImage(image)
    plt.imshow(np[int(np.size(np, 0) / 2), :, :])
    plt.show()


ROOT_PATH = f'/Volumes/SamsungT5/OPBG_Data/by_type/MB_by_sequence'
OUTPUT_PATH = f'/Volumes/SamsungT5/OPBG_Data/by_type/MB_registered'

dictionary = defaultdict(lambda: 0)

# Loops over patients.
for patient_code in filter(lambda path: not path.startswith('.'), os.listdir(ROOT_PATH)):
    logger.debug(f"Analyzing patient dir: {os.path.join(ROOT_PATH, patient_code)}")
    patient_path = os.path.join(ROOT_PATH, patient_code)
    patient_scans_paths = []

    # Loops over the scans of the patient.
    for patient_scan_number in os.listdir(patient_path):
        logger.debug(f"Sequence found in dir: {os.path.join(patient_code, patient_scan_number)}")
        patient_scans_paths.append(os.path.join(patient_code, patient_scan_number))

    # Finds the reference image inside of the patient folder and
    # returns an array with all the scans.
    scans, ref_scan_index = du.read_scans_and_find_ref_scan(patient_scans_paths)

    for s in scans:
       w, h, d = s.scan.GetWidth(), s.scan.GetHeight(), s.scan.GetDepth()
       t = (w, h, d)
       dictionary[t] += 1

for k, v in dictionary.items():
    print(k, v)




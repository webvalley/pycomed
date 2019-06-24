import pycomed

INPUT_PATH = "/Volumes/SamsungT5/OPBG_Data/by_type/MB_SMALL"
OUTPUT_PATH = "/Volumes/SamsungT5/OPBG_Data/by_type/MB_ORGANIZED"
REGISTERED_PATH = "/Volumes/SamsungT5/OPBG_Data/by_type/MB_REGISTERED"

dataset_organizer = pycomed.DICOMDatasetOrganizer(input_path=INPUT_PATH, output_path=OUTPUT_PATH)
dataset_reader = pycomed.DICOMDatasetReader(dataset_organizer)

fixed_image = dataset_reader.get_fixed_image("OPBG0001")
moving_image = dataset_reader.get_scans()[0]

moving_image.perform_registration(fixed_image, REGISTERED_PATH)




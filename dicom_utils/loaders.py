import os
from datetime import datetime

import SimpleITK as sitk
import numpy as np
import pydicom
from skimage.draw import polygon


def load_series(folder, metadata=False):
    '''
    Load a series of DCM slices from the folder.
    Return a dictionary: 
        'image': SimpleITK image of the 3D scan; 
        'metadta': slice image with metadata.
    '''
    reader = sitk.ImageSeriesReader()
    reader.LoadPrivateTagsOn()
    dicom_names = reader.GetGDCMSeriesFileNames(folder)
    reader.SetFileNames(dicom_names)
    try:
        image = reader.Execute()

        if metadata:
            files = os.listdir(folder)
            file_metadata = os.path.join(folder, files[0])
            reader = sitk.ImageFileReader()
            reader.LoadPrivateTagsOn()
            reader.SetFileName(file_metadata)

            image_w_metadata = reader.Execute()

            return (image, image_w_metadata)
        else:
            return (image)
    except RuntimeError:
        print(f"An error occurred while reading the dicom file in {folder}.")
        return None


def load_roi(file, roi_name, image):
    '''
    Load a DCM file (RTSTRUCT modality) containing volume ROIs.
    Return a dictionary for the selected roi names (all rois if name=None):
        'image': names of the ROIs; 
        'coords': coordinates of the ROIs;
        'box': coordinate of the bounding box of each ROI;
        'reference': reference dicom dataset with metadata (if return_ref=True).
    '''

    mask = sitk.Image(image.GetSize(), sitk.sitkFloat32)
    mask.CopyInformation(image)

    dataset = pydicom.dcmread(file)

    structure_set = dataset.StructureSetROISequence
    rois = dataset.ROIContourSequence

    for i, (STRUCT, ROI) in enumerate(zip(structure_set, rois)):
        if STRUCT.ROIName == roi_name:
            contours = ROI.ContourSequence
            coords = []
            for Z_CONT in contours:
                z_data = np.array([float(x) for x in Z_CONT.ContourData])
                z_data = np.reshape(z_data, (int(len(z_data) / 3), 3))
                coords.append(z_data)

    for zslice in coords:
        x_ = []
        y_ = []
        for point in zslice:
            idx_x, idx_y, idx_z = image.TransformPhysicalPointToIndex(point)
            x_.append(idx_x)
            y_.append(idx_y)
        rr, cc = polygon(np.array(y_), np.array(x_))
        for R, C in zip(rr, cc):
            mask[int(C), int(R), int(idx_z)] = 1

    return (mask)


# %%
def __str__(x):
    return (str(int(float(x))))


def __get_SUVfactor_BQML(dataset):
    #    print(dataset)
    dataset_keys = list(dataset.keys())
    try:
        radio_info_sequence = dataset[0x0054, 0x0016][0]
    except:
        print('Unable to obtain Radiological Information Sequence, returning SUVbwfactor=1')
        return (1)
    radio_info_keys = list(radio_info_sequence.keys())

    try:
        total_dose = radio_info_sequence[0x0018, 0x1074].value
    except:
        print('Unable to obtain total dose, returning SUVbwfactor=1')
        return (1)

    try:
        half_life = radio_info_sequence[0x0018, 0x1075].value  # seconds
    except:
        print('Unable to obtain half_life dose, returning SUVbwfactor=1')
        return (1)

    try:
        patient_weight = float(dataset[0x0010, 0x1030].value)
    except:
        patient_weight = 70.

        # -------------------------------------
    # check consistency of datetime info
    series_date = __str__(dataset[0x0008, 0x0021].value)
    series_time = __str__(dataset[0x0008, 0x0031].value)
    series_dt = datetime.strptime(series_date + series_time, '%Y%m%d%H%M%S')

    # check that acquis_dt is after series_dt, otherwise: SEE PSEUDOCODE
    acquis_date = __str__(dataset[0x0008, 0x0022].value)
    acquis_time = __str__(dataset[0x0008, 0x0032].value)
    acquis_dt = datetime.strptime(acquis_date + acquis_time, '%Y%m%d%H%M%S')

    if series_dt <= acquis_dt:
        scan_dt = series_dt
    elif series_dt > acquis_dt:
        if (
                '0x0009',
                '0x100d') in dataset_keys:  # if GE private scan Date and Time (0x0009,0x100d,“GEMS_PETD_01”) present
            scan_dt = datetime.strptime(__str__(dataset[0x0009, 0x100d].value),
                                        '%Y%m%d%H%M%S')  # scan Date and Time = GE private scan Date and Time (0x0009,0x100d,“GEMS_PETD_01”)
        else:
            # TODO: implement may be Siemens series w/ altered Series Date and Time
            print(f'Inconsistent date times: Acquis: {acquis_dt} - Series: {series_dt}')
            scan_dt = series_dt

    # Scan dt is the start of the image acquisition (so far)
    # -------------------------------------
    # obtain start of infusion
    if ('0009', '100d') in dataset_keys and ('0009', '103b') in dataset_keys:
        injection_dt = datetime.strptime(__str__(dataset[0x0009, 0x103b].value), '%Y%m%d%H%M%S')
        scan_dt = datetime.strptime(__str__(dataset[0x0009, 0x100d].value), '%Y%m%d%H%M%S')
    elif ('0018', '1078') in radio_info_keys:
        injection_dt = datetime.strptime(__str__(radio_info_sequence[0x0018, 0x1078].value), '%Y%m%d%H%M%S')
    elif ('0018', '1072') in radio_info_keys:
        print('Decay time derived from radio info sequence, check spanning midnight')
        injection_time = radio_info_sequence[0x0018, 0x1072].value
        injection_dt = datetime.strptime(series_date + injection_time,
                                         '%Y%m%d%H%M%S')  # start Date is not explicit ... assume same as Series Date; but consider spanning midnight
        # TODO: check spanning midnight
    else:
        print('Unable to obtain infusion datetime, using decay time = 0')
        injection_dt = scan_dt

    decay_time = scan_dt - injection_dt
    if decay_time.days < 0:
        print(f'Non positive decay time: using 0. Injection: {injection_dt} - Scan {scan_dt}')
        decay_time = 0
    else:
        decay_time = decay_time.seconds
    decayed_dose = total_dose * np.power(2,
                                         -decay_time / half_life)  # Radionuclide Total Dose is NOT corrected for residual dose in syringe, which is ignored here
    SUVbwScaleFactor = (patient_weight * 1000 / decayed_dose)
    return (SUVbwScaleFactor)


def __get_SUVfactor_CNTS(dataset):
    dataset_keys = list(dataset.keys())
    if ('0x7053', '0x1000') in dataset_keys:
        SUVbwScaleFactor = float(dataset[0x7053, 0x1000].value)  # ,“ Philips PET Private Group”)
    elif ('0x7053', '0x1009') in dataset_keys:
        # if (0x7053,0x1000) not present, but (0x7053,0x1009) is present, then (0x7053,0x1009) * Rescale Slope scales pixels to Bq/ml, and proceed as if Units are BQML
        SUVbwScaleFactor = float(dataset[0x7053, 0x1009].value) * __get_SUVfactor_BQML(
            dataset)  # *rescale_slope: last factor is considered when loading each slice independently
    else:
        print('Unable to obtain SUVbwScaleFactor, returning 1')
        SUVbwScaleFactor = 1

    return (SUVbwScaleFactor)


def load_SUV(folder):
    # https://qibawiki.rsna.org/index.php/Standardized_Uptake_Value_(SUV)
    # https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5228047/
    # get overall info:
    files = os.listdir(folder)
    PET_FILE = files[0]
    ref_ds = pydicom.dcmread(os.path.join(folder, PET_FILE))
    dataset_keys = list(ref_ds.keys())

    corrected_image = ref_ds[0x0028, 0x0051].value
    decay_correction = ref_ds[0x0054, 0x1102].value
    units = ref_ds[0x0054, 0x1001].value

    assert 'ATTN' in corrected_image and 'DECY' in corrected_image and decay_correction == 'START', 'Missing conversion conditions'

    if units == 'BQML':
        SUVbwScaleFactor = __get_SUVfactor_BQML(ref_ds)
    elif units == 'CNTS':
        SUVbwScaleFactor = __get_SUVfactor_CNTS(ref_ds)
    elif units == 'GML':
        SUVbwScaleFactor = 1
    else:
        print(f'Units {units} not valid, using SUVbwScaleFactor=1')
        SUVbwScaleFactor = 1

    #  Now load and convert each slide independently, as it cannot be assumed the rescale slope be the same for all slices

    # load dimensions info
    nx = int(ref_ds.Rows)
    ny = int(ref_ds.Columns)
    nz = len(files)

    # create 3d numpy array of the scan
    ArrayDicom = np.zeros((nx, ny, nz))
    Locations = []

    # loop through all the DICOM files
    for i, filenameDCM in enumerate(files):
        # read the file
        ds = pydicom.dcmread(os.path.join(folder, filenameDCM))
        rescale_intercept = float(ds[0x0028, 0x1052].value)
        rescale_slope = float(ds[0x0028, 0x1053].value)

        if units == 'CNTS' and not ('0x7053', '0x1000') in dataset_keys and ('0x7053', '0x1009') in dataset_keys:
            rescale_slope = rescale_slope ** 2

        # store the raw image data
        ArrayDicom[:, :, i] = ((ds.pixel_array * rescale_slope) + rescale_intercept) * SUVbwScaleFactor
        Locations.append(float(ds.SliceLocation))

    indexes_sort = np.argsort(Locations)
    ArrayDicom = ArrayDicom[:, :, indexes_sort]

    scan = sitk.GetImageFromArray(np.transpose(ArrayDicom, (2, 0, 1)))
    scan_meta = load_series(folder)

    scan.CopyInformation(scan_meta)
    return (scan)

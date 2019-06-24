import os

import numpy as np
import pydicom


def flatten(x):
    out = np.array([])

    for X in x:
        X = np.array(X)
        out = np.r_[out, X]

    return (out)


def isDCMLeaf(directory, all_dcm=True):
    '''
    Return true if the directory contains only dcm file
    '''
    subdirs = [name for name in os.listdir(directory) if os.path.isdir(os.path.join(directory, name))]
    if len(subdirs) > 0:
        return (False)
    fileslist = os.listdir(directory)
    if all_dcm:
        return (np.array(['.dcm' in x for x in fileslist]).all())
    else:
        dcmCollection = np.array([1 if '.dcm' in x else 0 for x in fileslist])
        return (sum(dcmCollection) / len(fileslist) > 0.9)


def isRTSTRUCT(folder):
    if not isDCMLeaf(folder): return (False)

    files = os.listdir(folder)
    if len(files) != 1: return (False)

    dataset = pydicom.dcmread(os.path.join(folder, files[0]))
    if dataset.Modality != 'RTSTRUCT': return (False)

    return (True)


def get_DCMLeaf_info(directory, all_dcm=True):
    '''
    Return number of files and modality of a DCMLeaf directory
    '''
    assert isDCMLeaf(directory, all_dcm), 'directory should be a DCMLeaf'
    files = os.listdir(directory)
    try:
        RefDs = pydicom.dcmread(os.path.join(directory, files[0]))
        modality = RefDs.Modality
    except:
        modality = ''
    return (len(files), modality)


def get_dataset_info(dcm_dataset):
    '''
    Read and print all string metadata
    '''
    tags = dcm_dataset.dir()
    for TAG in tags:
        value = dcm_dataset.get(TAG)
        if isinstance(value, str) or isinstance(value, float) or isinstance(value, int):
            print(TAG, '\t\t\t', str(value))


def iterativeScan(directory, all_dcm=True):
    '''
    Iteratively scan all folders and sub-folders and report info about the DCMLeaf folders
    '''
    if isDCMLeaf(directory, all_dcm):
        leaf_info = get_DCMLeaf_info(directory, all_dcm)
        return (directory, leaf_info[0], leaf_info[1])
    else:
        directories = []
        n_slices = []
        modalities = []
        subdirs = [os.path.join(directory, name) for name in os.listdir(directory) if
                   os.path.isdir(os.path.join(directory, name))]
        for SUB in subdirs:
            subdir, n_slice, modality = iterativeScan(SUB, all_dcm)
            directories.append(np.array(subdir))
            n_slices.append(np.array(n_slice))
            modalities.append(np.array(modality))
        return (directories, n_slices, modalities)


def get_rois_names(folder):
    '''
    Load a DCM file (RTSTRUCT modality) containing volume ROIs and return the names of the ROIs
    '''
    assert isRTSTRUCT(folder), "Input folder is not a valid RTSTRUCT folder"
    files = os.listdir(folder)
    dataset = pydicom.dcmread(os.path.join(folder, files[0]))

    structure_set = dataset.StructureSetROISequence
    rois = dataset.ROIContourSequence

    roi_name = []
    for i, (STRUCT, ROI) in enumerate(zip(structure_set, rois)):
        roi_name.append(STRUCT.ROIName)

    return (roi_name)

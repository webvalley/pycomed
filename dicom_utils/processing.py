import SimpleITK as sitk
import numpy as np


def to_numpy(image, size=None):
    image_np = sitk.GetArrayFromImage(image)

    if size is not None:
        differences = np.array([int((size[i] - image_np.shape[i]) / 2) for i in range(3)])
        starts_out = differences.copy()
        starts_out[differences < 0] = 0
        starts_in = differences
        starts_in[differences > 0] = 0
        starts_in = abs(starts_in / 2).astype(int)
        out = np.mean(image_np) * np.ones(size)
        out[starts_out[0]: starts_out[0] + image_np.shape[0],
        starts_out[1]: starts_out[1] + image_np.shape[1],
        starts_out[2]: starts_out[2] + image_np.shape[2]] = image_np[starts_in[0]: starts_in[0] + size[0],
                                                            starts_in[1]: starts_in[1] + size[1],
                                                            starts_in[2]: starts_in[2] + size[2]]
        return (out)
    else:
        return (image_np)


def filter_outbounds(image, range_pixel):
    image = sitk.Threshold(image, lower=-2000, upper=range_pixel[1], outsideValue=range_pixel[1])
    image = sitk.Threshold(image, lower=range_pixel[0], upper=5000, outsideValue=range_pixel[0])
    return (image)


def resample(image, spacing=None, size=None, interpolator=sitk.sitkBSpline):
    assert spacing is not None or size is not None, "Either pixel_size or pixel_number should be defined, not both"
    assert not (
            spacing is not None and size is not None), "Either pixel_size or pixel_number should be defined, not both"

    origins = image.GetOrigin()
    spacing_orig = image.GetSpacing()
    size_orig = image.GetSize()

    dimX = spacing_orig[0] * size_orig[0]
    dimY = spacing_orig[1] * size_orig[1]
    dimZ = spacing_orig[2] * size_orig[2]

    if spacing is not None:
        sizeX = int((dimX) / spacing[0])
        sizeY = int((dimY) / spacing[1])
        sizeZ = int((dimZ) / spacing[2])

        size = (sizeX, sizeY, sizeZ)

    elif size is not None:
        spaceX = dimX / size[0]  # Musk
        spaceY = dimY / size[1]
        spaceZ = dimZ / size[2]

        spacing = (spaceX, spaceY, spaceZ)

    target = sitk.Image(size, sitk.sitkFloat32)
    target.SetSpacing(spacing)
    target.SetOrigin(image.GetOrigin())

    out = sitk.Resample(image, target)
    return (out)


def get_bbox_vertices(segmentation, margin=5):
    segmentation_np = np.transpose(sitk.GetArrayFromImage(segmentation), (2, 1, 0))

    idx_1 = np.where(segmentation_np > 0)
    idx_st_X, idx_sp_X = int(np.min(idx_1[0])), int(np.max(idx_1[0]))
    idx_st_Y, idx_sp_Y = int(np.min(idx_1[1])), int(np.max(idx_1[1]))
    idx_st_Z, idx_sp_Z = int(np.min(idx_1[2])), int(np.max(idx_1[2]))

    start_mm = segmentation.TransformContinuousIndexToPhysicalPoint([idx_st_X, idx_st_Y, idx_st_Z])
    stop_mm = segmentation.TransformContinuousIndexToPhysicalPoint([idx_sp_X, idx_sp_Y, idx_sp_Z])

    # add margin
    start_mm = [x - margin for x in start_mm]
    stop_mm = [x + margin for x in stop_mm]

    return (start_mm, stop_mm)


def _start_outside(scan, start):
    origin = scan.GetOrigin()
    for i, (S, O) in enumerate(zip(start, origin)):
        if S < O:
            start[i] = O
    return (start)


def _stop_outside(scan, stop):
    origin = scan.GetOrigin()
    for i, (S, O) in enumerate(zip(stop, origin)):
        if S < O:
            stop[i] = O
    return (stop)


def extract_volume(scan, start_vertex, stop_vertex):
    start_vertex = _start_outside(scan, start_vertex)
    stop_vertex = _stop_outside(scan, stop_vertex)

    idx_start = scan.TransformPhysicalPointToIndex(start_vertex)
    idx_stop = scan.TransformPhysicalPointToIndex(stop_vertex)
    scan_volume = scan[idx_start[0]:idx_stop[0],
                  idx_start[1]:idx_stop[1],
                  idx_start[2]:idx_stop[2]]
    return (scan_volume)

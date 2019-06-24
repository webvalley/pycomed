import SimpleITK as sitk
import numpy as np


# FROM: https://github.com/SimpleITK/SPIE2018_COURSE
# %
def eul2quat(ax, ay, az, atol=1e-8):
    '''
    Translate between Euler angle (ZYX) order and quaternion representation of a rotation.
    Args:
        ax: X rotation angle in radians.
        ay: Y rotation angle in radians.
        az: Z rotation angle in radians.
        atol: tolerance used for stable quaternion computation (qs==0 within this tolerance).
    Return:
        Numpy array with three entries representing the vectorial component of the quaternion.

    '''
    # Create rotation matrix using ZYX Euler angles and then compute quaternion using entries.
    cx = np.cos(ax)
    cy = np.cos(ay)
    cz = np.cos(az)
    sx = np.sin(ax)
    sy = np.sin(ay)
    sz = np.sin(az)
    r = np.zeros((3, 3))
    r[0, 0] = cz * cy
    r[0, 1] = cz * sy * sx - sz * cx
    r[0, 2] = cz * sy * cx + sz * sx

    r[1, 0] = sz * cy
    r[1, 1] = sz * sy * sx + cz * cx
    r[1, 2] = sz * sy * cx - cz * sx

    r[2, 0] = -sy
    r[2, 1] = cy * sx
    r[2, 2] = cy * cx

    # Compute quaternion:
    qs = 0.5 * np.sqrt(r[0, 0] + r[1, 1] + r[2, 2] + 1)
    qv = np.zeros(3)
    # If the scalar component of the quaternion is close to zero, we
    # compute the vector part using a numerically stable approach
    if np.isclose(qs, 0.0, atol):
        i = np.argmax([r[0, 0], r[1, 1], r[2, 2]])
        j = (i + 1) % 3
        k = (j + 1) % 3
        w = np.sqrt(r[i, i] - r[j, j] - r[k, k] + 1)
        qv[i] = 0.5 * w
        qv[j] = (r[i, j] + r[j, i]) / (2 * w)
        qv[k] = (r[i, k] + r[k, i]) / (2 * w)
    else:
        denom = 4 * qs
        qv[0] = (r[2, 1] - r[1, 2]) / denom;
        qv[1] = (r[0, 2] - r[2, 0]) / denom;
        qv[2] = (r[1, 0] - r[0, 1]) / denom;
    return qv


def __rototranscale_random_parameters(thetaXrange=[-np.pi / 18.0, np.pi / 18.0],
                                      thetaYrange=[-np.pi / 18.0, np.pi / 18.0],
                                      thetaZrange=[-np.pi / 18.0, np.pi / 18.0],
                                      tXrange=[-2, 2],
                                      tYrange=[-2, 2],
                                      tZrange=[-2, 2],
                                      scalerange=[0.9, 1.3]):
    thetaX = np.random.uniform(thetaXrange[0], thetaXrange[1])
    thetaY = np.random.uniform(thetaYrange[0], thetaYrange[1])
    thetaZ = np.random.uniform(thetaZrange[0], thetaZrange[1])

    tX = np.random.uniform(tXrange[0], tXrange[1])
    tY = np.random.uniform(tYrange[0], tYrange[1])
    tZ = np.random.uniform(tZrange[0], tZrange[1])

    scale = np.random.uniform(scalerange[0], scalerange[1])

    return (list(eul2quat(thetaX, thetaY, thetaZ)) + [tX, tY, tZ, scale])


def __radialdistort_random_parameters(k1range=[1e-7, 1e-5],
                                      k2range=[1e-15, 1e-12],
                                      k3range=[1e-15, 1e-12]):
    k1 = np.random.uniform(k1range[0], k1range[1])
    k2 = np.random.uniform(k2range[0], k2range[1])
    k3 = np.random.uniform(k3range[0], k3range[1])

    return (k1, k2, k3)


# %
def rototranscale_transform(image):
    aug_transform = sitk.Similarity3DTransform()
    reference_center = np.array(image.TransformContinuousIndexToPhysicalPoint(np.array(image.GetSize()) / 2.0))
    aug_transform.SetCenter(reference_center)
    aug_transform.SetParameters(__rototranscale_random_parameters())
    return (aug_transform)


def radialdistort_transform(image, distortion_center=None):
    c = distortion_center
    if not c:  # The default distortion center coincides with the image center
        c = np.array(image.TransformContinuousIndexToPhysicalPoint(np.array(image.GetSize()) / 2.0))
    k1, k2, k3 = __radialdistort_random_parameters()
    # Compute the vector image (p_d - p_c) 
    delta_image = sitk.Image(image.GetSize(), sitk.sitkVectorFloat64)
    delta_image.CopyInformation(image)
    index_ranges = [np.arange(0, i) for i in image.GetSize()]
    for indexes in np.nditer(np.meshgrid(*index_ranges)):
        index = tuple(map(np.asscalar, indexes))
        delta_image[index] = np.array(image.TransformContinuousIndexToPhysicalPoint(index)) - c
    delta_image_components = [sitk.VectorIndexSelectionCast(delta_image, index) for index in
                              range(image.GetDimension())]

    # Compute the radial distortion expression
    r2_image = sitk.Image(image.GetSize(), sitk.sitkFloat64)
    r2_image.CopyInformation(image)
    for img in delta_image_components:
        r2_image += img ** 2
    r4_image = r2_image ** 2
    r6_image = r2_image * r4_image
    disp_image = k1 * r2_image + k2 * r4_image + k3 * r6_image
    displacement_image = sitk.Compose([disp_image * img for img in delta_image_components])

    displacement_field_transform = sitk.DisplacementFieldTransform(displacement_image)
    return (displacement_field_transform)


def augment_morph(image_list):
    ref_image = image_list[0]
    T1 = rototranscale_transform(ref_image)
    #    T2 = radialdistort_transform(ref_image)

    aug_image_list = []
    for image in image_list:
        out_value = int(100 * np.nanmedian(sitk.GetArrayViewFromImage(image))) / 100
        aug_image = sitk.Resample(image, image, T1, sitk.sitkBSpline, out_value)
        #        aug_image = sitk.Resample(aug_image, aug_image, T2)
        aug_image_list.append(aug_image)
    return (aug_image_list)


def get_gauss_noise():
    sd = np.random.uniform(0, 0.1)
    f_gauss = sitk.AdditiveGaussianNoiseImageFilter()
    f_gauss.SetStandardDeviation(sd)
    return (f_gauss)


def get_histo_equal():
    alpha = np.random.uniform(.7, 1)
    beta = np.random.uniform(.7, 1)
    f_histo = sitk.AdaptiveHistogramEqualizationImageFilter()
    f_histo.SetAlpha(alpha)
    f_histo.SetBeta(beta)
    return (f_histo)


def augment_intensity(image_list):
    filters = [get_histo_equal(), get_gauss_noise()]

    aug_image_list = []
    for aug_image in image_list:
        for f in filters:
            aug_image = f.Execute(aug_image)
        aug_image_list.append(aug_image)
    return (aug_image_list)

##%%    
#
# TEST_DATA_FILE = '/home/andrea/Trento/Lavori/BraTS/results/bbox/Brats18_2013_2_1/T2.mha'
#
# image = sitk.ReadImage(TEST_DATA_FILE)
#
#
# image_out = augment_morph([image])

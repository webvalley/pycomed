from setuptools import setup

setup(name='dicom_utils',
      version='0.1',
      url='https://gitlab.fbk.eu/bizzego/dicom_utils',
      description='Utilities to work with DICOM data',
      packages=['dicom_utils'],
      install_requires=[
          'numpy',
          'scipy',
          'scikit-image',
          'pydicom'
      ],
      zip_safe=False)

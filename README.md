
# Documentation for `pycomed`
## Organizing the dataset
In order to work with `pycomed`, your dataset needs to be specifically formatted following a schema used by `pycomed` to efficientely query all the data for you. Pycomed provides you with a specific class used to organize the dataset automatically for you. The organizer class needs two parameters: the input_path which is the path of the unorganized dataset and the output_path which is the folder in which your organized dataset files will be copied (currently pycomed copies the files and not moves them).


```python
import pycomed.io

dataset_organizer = pycomed.io.DICOMDatasetOrganizer(input_path="My input path", output_path="My output path")
```

## Reading the dataset
After the organizer has been setted up we need to attach it to the reader which is a class responsible of providing methods to query data from your dataset with ease.


```python
dataset_reader = pycomed.io.DICOMDatasetReader(dataset_organizer)
```

### The scan object
`pycomed` works with an internal object which has a base it's a Scan object that has different childs depeding on the scan type you are querying. For example `pycomed` has the DICOMScan which is the Scan object specifically created to manage DICOM files. Every time you read data with the reader you will get a list of scan objects that vary depeding on the type of the reader.

### Getting all the scans
If you want to get all the scans of the dataset use the following code:


```python
scans = dataset_reader.get_scans()
```

### Getting scans via filter function
If you want more control on how the scans are filtered you can use the following code:


```python
import pydicom

# The function will have as an argument the path of the scan and it must return true or false, where true tells
# the reader to keep that scan, otherwise it will skip it.
def filter_function(scan_path):
    scan = pydicom.dcmread(scan_path)
    return scan.SeriesNumber == 10

scans = dataset_reader.get_scans(filter_function)
```

### Getting scans by patient name
If you want to get all the scans of a specific patient use the following code:


```python
scans = dataset_reader.get_scans_by_patient_name("Patient name")
```

### Getting scans by acquisition date
If you want to get all the scans acquiried between a date interval use the following code:


```python
import datetime

# The date must be formatted following this schema.
from_date = datetime.datetime.strptime("xxxxyyzz", "%Y%m%d")
to_date = datetime.datetime.strptime("xxxxyyzz", "%Y%m%d")

scans = dataset_reader.get_scans_by_acquisition_date(from_date, to_date)
```

### Getting scans by dimensions
If you want to get all the scans with specific dimensions use the following code:


```python
width = 256
height = 256
depth = 30

scans = dataset_reader.get_scans_by_size(width, height, depth)
```

## Registration
`pycomed` features built-in registration functions to perform registration on scans with ease.
Currently `pycomed` uses the SimpleITK library to perform the registration and it is important to note that the result will be saved as a **nifti** file with _.nii_ extension.
```python
# Specify where the registered image will be saved.
REGISTERED_PATH = "/Volumes/SamsungT5/OPBG_Data/by_type/MB_REGISTERED"

# You can get the fixed image with the built-in method in the reader,
# otherwise you can choose which image you prefer.
fixed_image = dataset_reader.get_fixed_image("OPBG0001")

# Get the moving image.
moving_image = dataset_reader.get_scans()[0]

# Perform registration of the moving image on top of the fixed image.
# Note that only specific scan types support registration, in this case the MRI scans.
# The function returns the output path where the registered image is saved as nifti so you can
# read it on your own.
output_path = moving_image.perform_registration(fixed_image, REGISTERED_PATH)

```

## Notes
`pycomed` is currently in development state, so you might encounter some bugs and missing features. Feel free to open issues if you have suggestions, improvements or bugs to report.

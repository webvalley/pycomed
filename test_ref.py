import dicom_utils as du

scan, ref_scan_index = du.read_scans_and_find_ref_scan(
    [f'/Volumes/LaCie/OPBG_Data/by_type/MB_by_sequence/OPBG0001_20180622_091540174/2',
     f'/Volumes/LaCie/OPBG_Data/by_type/MB_by_sequence/OPBG0001_20180622_091540174/3',
     f'/Volumes/LaCie/OPBG_Data/by_type/MB_by_sequence/OPBG0001_20180622_091540174/3',
     f'/Volumes/LaCie/OPBG_Data/by_type/MB_by_sequence/OPBG0001_20180622_091540174/4',
     f'/Volumes/LaCie/OPBG_Data/by_type/MB_by_sequence/OPBG0001_20180622_091540174/5',
     f'/Volumes/LaCie/OPBG_Data/by_type/MB_by_sequence/OPBG0001_20180622_091540174/6',
     f'/Volumes/LaCie/OPBG_Data/by_type/MB_by_sequence/OPBG0001_20180622_091540174/7',
     f'/Volumes/LaCie/OPBG_Data/by_type/MB_by_sequence/OPBG0001_20180622_091540174/8',
     f'/Volumes/LaCie/OPBG_Data/by_type/MB_by_sequence/OPBG0001_20180622_091540174/9',
     f'/Volumes/LaCie/OPBG_Data/by_type/MB_by_sequence/OPBG0001_20180622_091540174/10',
     f'/Volumes/LaCie/OPBG_Data/by_type/MB_by_sequence/OPBG0001_20180622_091540174/11'])

print(ref_scan_index)

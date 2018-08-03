import os

dir = '/path/to/folder/of/tifs'

for file in os.listdir(dir):
    file_path = os.path.join(dir, file)
    try:
        if os.path.isfile(file_path):
            sfx = file_path[-4:]
            if sfx != '.tif':
                print('deleting: ', file_path)
                os.remove(file_path)

    except Exception as e:
        print(e)

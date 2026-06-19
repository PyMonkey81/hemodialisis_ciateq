import versioneer   

def generate_version_file(outfile='file_version_info.txt'):
    version = versioneer.get_version()
    with open(outfile, 'w') as f:
        f.write(version)
    print(f"Version {version} written to {outfile}")
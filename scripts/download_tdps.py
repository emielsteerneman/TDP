import wget
import os
import re

tdp_download_urls = [
    "https://ssl.robocup.org/wp-content/uploads/2023/07/TDPs_2023.zip",
    "https://ssl.robocup.org/wp-content/uploads/2022/04/TDPs_2022.zip",
    "https://ssl.robocup.org/wp-content/uploads/2020/03/2020_DivA_ETDPs.zip",
    "https://ssl.robocup.org/wp-content/uploads/2020/03/2020_DivB_TDPs.zip",
    "https://ssl.robocup.org/wp-content/uploads/2019/03/TDPs_2019.zip",
    "https://ssl.robocup.org/wp-content/uploads/2019/01/TDPs_2018.zip",
    "https://ssl.robocup.org/wp-content/uploads/2019/01/TDPs_2017.zip",
    "https://ssl.robocup.org/wp-content/uploads/2019/01/TDPs_2016.zip",
    "https://ssl.robocup.org/wp-content/uploads/2019/01/TDPs_2015.zip",
    "https://ssl.robocup.org/wp-content/uploads/2019/01/TDPs_2014.zip",
    "https://ssl.robocup.org/wp-content/uploads/2019/01/TDPs_2013.zip",
    "https://ssl.robocup.org/wp-content/uploads/2020/02/TDPs_2012.zip",
    "https://ssl.robocup.org/wp-content/uploads/2019/01/TDPs_2011.zip",
    "https://ssl.robocup.org/wp-content/uploads/2019/01/TDPs_2010.zip",
    "https://ssl.robocup.org/wp-content/uploads/2020/02/TDPs_2009.zip",
]

tdp_renaming = {
    "2009/2009_ETDP_b-smart.pdf": "2009/2009_ETDP_B-Smart.pdf",
    "2009/2009_ETDP_ZJUNLICT.pdf": "2009/2009_ETDP_ZJUNlict.pdf",
    "2009/2009_TDP_b-smart.pdf": "2009/2009_TDP_B-Smart.pdf",
    "2009/2009_TDP_erforce.pdf": "2009/2009_TDP_ER-Force.pdf",
    "2012/2012_ETDP_skuba.pdf": "2012/2012_ETDP_Skuba.pdf",
    "2012/2012_ETDP_zjunlict.pdf": "2012/2012_ETDP_ZJUNlict.pdf",
    "2012/2012_TDP_erforce.pdf": "2012/2012_TDP_ER-Force.pdf",
    "2012/2012_TDP_omid.pdf": "2012/2012_TDP_OMID.pdf",
    "2012/2012_TDP_rfc_cambridge.pdf": "2012/2012_TDP_RFC_Cambridge.pdf",
    "2012/2012_TDP_robofei.pdf": "2012/2012_TDP_RoboFEI.pdf",
    "2012/2012_TDP_ubc_thunderbots.pdf": "2012/2012_TDP_UBC_Thunderbots.pdf",
    "2017/2017_TDP_Op-Amp.pdf": "2017/2017_TDP_OP-Amp.pdf",
    "2019/2019_ETDP_OP-AmP.pdf": "2019/2019_ETDP_OP-Amp.pdf",
    "2019/2019_TDP_ITAndroids_Small_Size.pdf": "2019/2019_TDP_ITAndroids.pdf",
    "2020/2020_ETDP_ERForce.pdf": "2020/2020_ETDP_ER-Force.pdf",
    "2020/2020_ETDP_RTT.pdf": "2020/2020_ETDP_RoboTeam_Twente.pdf",
    "2020/2020_ETDP_TIGERS.pdf": "2020/2020_ETDP_TIGERs_Mannheim.pdf",
    "2020/2020_TDP_Sysmic.pdf": "2020/2020_TDP_Sysmic_Robotics.pdf",
    "2020/2020_TDP_Warthog.pdf": "2020/2020_TDP_Warthog_Robotics.pdf",
    "2022/2022_ETDP_RoboTeam-Twente.pdf": "2022/2022_ETDP_RoboTeam_Twente.pdf",
    "2022/2022_ETDP_TIGERs-Mannheim.pdf": "2022/2022_ETDP_TIGERs_Mannheim.pdf",
    "2022/2022_TDP_UBC-Thunderbots.pdf": "2022/2022_TDP_UBC_Thunderbots.pdf"
}

tdp_output_dir = "TDPs"
# Create output directory if it doesn't exist
os.makedirs(tdp_output_dir, exist_ok=True)

print("\nDownloading TDPs...")
# Download TDPs and place in TDPs directory
for url in tdp_download_urls:
    filename = os.path.basename(url)
    # Check if file already exists
    if os.path.exists(os.path.join(tdp_output_dir, filename)):
        print(f"  File {filename} already exists, skipping download.")
        continue
    
    print(f"Downloading {url}...")
    wget.download(url, out=tdp_output_dir)

    # Convert filename to year
    year = re.findall('\d{4}', filename)[0]
    # Create directory for year if it doesn't exist
    os.makedirs(os.path.join(tdp_output_dir, year), exist_ok=True)
    # Extract zipfile to year directory
    print(f"\nExtracting {filename} to {year}...")
    os.system(f"unzip -o {os.path.join(tdp_output_dir, filename)} -d {os.path.join(tdp_output_dir, year)}")
    
print("All TDPs downloaded\n")

print("Renaming TDPs...")
# Manually correct some entries
for old_filename, new_filename in tdp_renaming.items():
    # First, check if file exists / is not already renamed
    if not os.path.exists(os.path.join(tdp_output_dir, old_filename)):
        # Skipping renaming since the file doesn't exist at the old location
        # Does it exist at the new location?
        if not os.path.exists(os.path.join(tdp_output_dir, new_filename)):
            print(f"Warning! File {os.path.basename(new_filename)} is missing!")
        continue
    
    # Rename file
    print(f"Renaming {old_filename} to {new_filename}...")
    os.rename(os.path.join(tdp_output_dir, old_filename), os.path.join(tdp_output_dir, new_filename))
print("All TDPs renamed\n")
if [ -z $1 ]
	then
		echo "Usage: ./download_tdps_from_azure.sh [output_directory]"
		echo "! Please provide a directory to download the tdps into"
		exit 1
fi

mkdir $1 && az storage blob download-batch --pattern "*.pdf" -d $1 -s https://tdps.blob.core.windows.net/tdps
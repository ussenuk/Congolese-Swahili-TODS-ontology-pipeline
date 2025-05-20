#!/bin/bash
# Install and configure Apache Jena Fuseki with correct Java version compatibility

# Function to install Java
install_java() {
    local version=$1
    echo "Installing Java $version..."
    
    if command -v apt-get &> /dev/null; then
        # Debian/Ubuntu
        if [ "$version" = "17" ]; then
            sudo apt-get update
            sudo apt-get install -y openjdk-17-jdk
        elif [ "$version" = "11" ]; then
            sudo apt-get update
            sudo apt-get install -y openjdk-11-jdk
        fi
    elif command -v dnf &> /dev/null; then
        # Fedora/RHEL/CentOS
        if [ "$version" = "17" ]; then
            sudo dnf install -y java-17-openjdk-devel
        elif [ "$version" = "11" ]; then
            sudo dnf install -y java-11-openjdk-devel
        fi
    else
        echo "Unsupported package manager. Please install Java $version manually."
        exit 1
    fi
    
    echo "Java $version installed successfully!"
}

# Ask user if they want to update Java
echo "Apache Jena Fuseki Installation Script"
echo "-------------------------------------"
echo "Fuseki 5.x requires Java 17+, while Fuseki 4.x requires Java 11+"

# Check Java version
if command -v java &> /dev/null; then
    java_version=$(java -version 2>&1 | awk -F '"' '/version/ {print $2}')
    java_major_version=$(echo $java_version | cut -d'.' -f1)
    echo "Detected Java version: $java_version (major version: $java_major_version)"
    
    # Ask if user wants to update Java
    read -p "Do you want to update Java? (y/n): " update_java
    if [[ "$update_java" == "y" || "$update_java" == "Y" ]]; then
        echo "1) Install Java 17 (required for Fuseki 5.x)"
        echo "2) Install Java 11 (required for Fuseki 4.x)"
        read -p "Select an option (1-2): " java_option
        
        case $java_option in
            1)
                install_java 17
                java_major_version=17
                ;;
            2)
                install_java 11
                java_major_version=11
                ;;
            *)
                echo "Invalid option. Continuing with current Java version."
                ;;
        esac
    fi
else
    echo "Java not detected. Installation required."
    echo "1) Install Java 17 (required for Fuseki 5.x)"
    echo "2) Install Java 11 (required for Fuseki 4.x)"
    read -p "Select an option (1-2): " java_option
    
    case $java_option in
        1)
            install_java 17
            java_major_version=17
            ;;
        2)
            install_java 11
            java_major_version=11
            ;;
        *)
            echo "Invalid option. Exiting."
            exit 1
            ;;
    esac
fi

# Set Fuseki version based on Java version
if [ "$java_major_version" -ge 17 ]; then
    # For Java 17+, use latest Fuseki
    fuseki_version="5.4.0"
    echo "Using Fuseki version $fuseki_version compatible with Java 17+"
elif [ "$java_major_version" -ge 11 ]; then
    # For Java 11-16, use Fuseki 4.x
    fuseki_version="4.8.0"
    echo "Using Fuseki version $fuseki_version compatible with Java 11-16"
else
    echo "Error: Your Java version $java_version is too old."
    echo "Fuseki 4.x requires Java 11+, and Fuseki 5.x requires Java 17+"
    echo "Please install a newer version of Java and try again."
    exit 1
fi

# Download and extract Fuseki
fuseki_name="apache-jena-fuseki-$fuseki_version"
fuseki_zip="$fuseki_name.zip"

# Determine download URL
if [ "$fuseki_version" = "5.4.0" ]; then
    download_url="https://dlcdn.apache.org/jena/binaries/$fuseki_zip"
else
    download_url="https://archive.apache.org/dist/jena/binaries/$fuseki_zip"
fi

# Download Fuseki if not already downloaded
if [ ! -f "$fuseki_zip" ]; then
    echo "Downloading $fuseki_name from $download_url"
    wget "$download_url"
else
    echo "$fuseki_zip already downloaded"
fi

# Extract Fuseki if not already extracted
if [ ! -d "$fuseki_name" ]; then
    echo "Extracting $fuseki_zip"
    unzip "$fuseki_zip"
else
    echo "$fuseki_name already extracted"
fi

# Make server script executable
chmod +x "$fuseki_name/fuseki-server"

echo "
Installation complete! You can start Fuseki with:

cd $fuseki_name
./fuseki-server --mem /humanitarian
"

# Add instructions for setting up as a service
echo "
To set up Fuseki as a service on startup:

1. Create a dedicated user for Fuseki:
   sudo useradd -m -d /opt/fuseki fuseki

2. Move Fuseki to a system location:
   sudo mkdir -p /opt/fuseki
   sudo cp -r $fuseki_name/* /opt/fuseki/
   sudo chown -R fuseki:fuseki /opt/fuseki

3. Create a systemd service file:
   sudo nano /etc/systemd/system/fuseki.service

   Add the following content:
   [Unit]
   Description=Apache Jena Fuseki SPARQL Server
   After=network.target

   [Service]
   Type=simple
   User=fuseki
   Group=fuseki
   ExecStart=/opt/fuseki/fuseki-server --mem /humanitarian
   WorkingDirectory=/opt/fuseki
   Restart=on-failure

   [Install]
   WantedBy=multi-user.target

4. Enable and start the service:
   sudo systemctl daemon-reload
   sudo systemctl enable fuseki
   sudo systemctl start fuseki

5. Check the status:
   sudo systemctl status fuseki
" 
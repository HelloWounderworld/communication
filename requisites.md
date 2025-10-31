# ⚙️ Requirements to Meet Before Working with Docker Containers and Azure

## 📋 Prerequisites

Before you begin, please ensure the following:

* 🐳 Docker is installed on the Server.
* 🎮 Docker is compatible with NVIDIA:

  * 🔧 The NVIDIA Container Toolkit is installed ([installation guide](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)).
  * 🚀 The GPU driver is up to date.

Below are the detailed steps to meet all the listed prerequisites.

---
## 🐳 1. Install Docker on Your Server

For Ubuntu/Debian, follow the official Docker instructions:
👉 [Install Docker Engine](https://docs.docker.com/engine/install/ubuntu/)

---

## 🎮 2. Enable NVIDIA GPU Support in Docker

### 🧪 Check if NVIDIA runtime is already configured:

```bash
docker info | grep "Runtimes"
```

Expected output:

```
Runtimes: nvidia runc
```

### 🖥️ Test GPU Availability:

```bash
nvidia-smi
```

Expected output:

```
+-----------------------------------------------------------------------------+
| NVIDIA-SMI 560.41     Driver Version: 561.03      CUDA Version: 12.6       |
|-------------------------------+------------------+--------------------------|
| GPU  Name                     | Bus-Id           | Volatile Uncorr. ECC     |
|-------------------------------+------------------+--------------------------|
|  0  NVIDIA RTX 4050           | 00000000:01:00.0 | N/A                      |
|  Temp  27C  Power: 59W/125W   | Memory: 0MiB/6141MiB | GPU-Util: 0%        |
+-------------------------------+------------------+--------------------------+
```

If `nvidia-smi` fails, you need to install the driver.

---

## 🧩 [**3. Install NVIDIA Driver (Ubuntu)**](https://qiita.com/tmasada/items/f77808c870c829c076fa)

### 🚀 Step-by-step:

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install ubuntu-drivers-common alsa-utils
```

List available drivers:

```bash
ubuntu-drivers devices
```

Install the recommended one:

```bash
sudo apt install -y nvidia-driver-535  # (example)
sudo reboot
```

Confirm installation:

```bash
nvidia-smi
```

---

## 🔧 4. Install NVIDIA Container Toolkit

📚 [Official installation guide](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)

### 🐧 For Ubuntu:

```bash
# Add NVIDIA GPG key & repo
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | \
  sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg

curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
  sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

# Install Toolkit
sudo apt update
sudo apt install -y nvidia-container-toolkit

# Configure runtime
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

---

## 🧪 Test GPU Inside Docker

Run:

```bash
docker info | grep "Runtimes"
```

Expected:

```
Runtimes: io.containerd.runc.v2 nvidia runc
```

Run a GPU container:

```bash
docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi
```

---

## ✅ Summary

🎉 You're now fully set up!

| Requirement                      | Status |
| -------------------------------- | ------ |
| Docker Installed                 | ✅      |
| NVIDIA Driver Installed          | ✅      |
| NVIDIA Docker Runtime Configured | ✅      |

---

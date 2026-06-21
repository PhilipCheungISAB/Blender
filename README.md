# Blender Physics Simulation Suite / Blender 物理仿真集成项目

Bilingual: [English](#english) | [中文](#中文)

---

## English

This repository is a collection of professional physics-based 3D simulation tools built on Blender's API. It contains two main projects:

1. **Wall** (`Wall/`): Seismic masonry wall structural sway, deformation, and damage simulation.
2. **ChickenBone** (`ChickenBone/`): Procedural vertical alignment, scaling, and tensile testing simulation of a biological bone model.

---

### 1. Seismic Wall Simulation (`Wall/`)
This project is an automated 3D physics simulation engine designed to study structural deformation, brick-sliding (vertical sag), and collapse behaviors of masonry walls under seismic loading.
* **Concrete Frame Generation**: Procedurally builds foundations, columns, and beams using Blender's `bpy` and `bmesh`. Configures shape keys (`Sway_X`, `Sway_Y`) to simulate elastic structural swaying.
* **Masonry Wall Assembly**: Lays brick-by-layer arrays with micro-gaps to avoid initial physical penetrations.
* **Cohesive Constraints**: Sets up Generic 6-DOF constraints between adjacent bricks and kinematic anchors to simulate plastic-like material properties.
* **DIC Dataset Camera Array**: Sets up a stereoscopic camera array (Front L/R, Right L/R) targeting the wall panels to capture high-resolution imagery for Digital Image Correlation (DIC) displacement tracking.

To run:
```bash
# Activate the conda environment (optional)
conda activate building

# Execute via Blender CLI
& "C:\Program Files\Blender Foundation\Blender 4.5\blender.exe" --background --python Wall/scripts/build_scene_large_plastic_v4.py
```

---

### 2. Chicken Humerus Bone Tensile Simulation (`ChickenBone/`)
This project contains scripts to automate the physical loading and tensile simulation on a chicken humerus bone mesh model.
* **Mesh Import & Auto-Alignment**: Automatically imports the `.glb` bone model, samples vertices to find the longest axis, centers the bone at the origin, re-orients it vertically, and scales it to exactly 8cm.
* **Tensile Simulation Script** (`simulate_tensile.py`): Automates scene construction, materials, displacement setup, and tensile/loading physics testing.

To run:
```bash
# Execute via Blender CLI
& "C:\Program Files\Blender Foundation\Blender 4.5\blender.exe" --background --python ChickenBone/simulate_tensile.py
```

---

### Manual Deployment via Conda

#### Prerequisites
* **Blender 4.5** (or compatible) installed globally (typically `C:\Program Files\Blender Foundation\Blender 4.5\blender.exe`).
* Anaconda / Miniconda installed.

#### Step-by-Step Setup

1. **Create Conda Environment**
   Create a Python 3.10 environment named `building`:
   ```bash
   conda create -n building python=3.10 -y
   ```

2. **Activate the Environment**
   ```bash
   conda activate building
   ```

3. **Install Dependencies**
   If there are auxiliary script requirements (such as `pandas`, `numpy`, `customtkinter` etc.), install them from requirements.txt:
   ```bash
   pip install -r requirements.txt
   ```

---

## 中文

本仓库是一个基于 Blender Python API 构建的专业级三维物理动力学仿真集成项目，包含以下两个核心子项目：

1. **Wall** (`Wall/`)：砌体砖墙结构在地震荷载下的侧摆、滑移下沉及坍塌失效物理仿真。
2. **ChickenBone** (`ChickenBone/`)：生物骨骼模型的程序化对齐、比例缩放及拉伸力学试验仿真。

---

### 1. 砌体砖墙抗震物理仿真 (`Wall/`)
该项目是一个自动化的三维物理动力学仿真引擎，旨在研究砌体砖墙在地震荷载下的结构变形、滑移（下沉）以及倒塌失效行为。
* **混凝土框架程序化生成**：基于 Blender 内置的 `bpy` 和 `bmesh` 自动生成柱梁框架，并配置形态键（Shape Key）模拟弹性摆动。
* **砌体砖墙装配**：按层交替铺设砖块阵列并留有微小砖缝，防止初始接触穿模导致物理引擎崩溃。
* **粘结网络构建**：在相邻砖块间架设六自由度（6-DOF）通用约束连接，以拟合剪切、压弯塑性力学响应。
* **双目 DIC 相机阵列**：架设双目相机组合，用于渲染输出可供数字图像相关法（DIC）算法分析的三维变形高清图序列。

运行指令：
```bash
# 激活 conda 辅助环境（可选）
conda activate building

# 通过 Blender 命令行执行仿真脚本
& "C:\Program Files\Blender Foundation\Blender 4.5\blender.exe" --background --python Wall/scripts/build_scene_large_plastic_v4.py
```

---

### 2. 鸡骨骼拉伸力学仿真 (`ChickenBone/`)
该子项目实现了针对鸡肱骨（Humerus）模型拉伸试验的仿真分析脚本。
* **模型导入与自动对齐**：自动读取 `.glb` 骨骼文件，通过顶点采样定位骨长主轴，使模型自动垂直居中，并精确缩放至 8 厘米高度。
* **拉伸测试仿真脚本** (`simulate_tensile.py`)：程序化完成测试场景、材质渲染、位移加载设置以及物理受力仿真。

运行指令：
```bash
# 通过 Blender 命令行执行拉伸仿真脚本
& "C:\Program Files\Blender Foundation\Blender 4.5\blender.exe" --background --python ChickenBone/simulate_tensile.py
```

---

### 使用 Conda 进行手动部署

#### 前提条件
* 系统中已全局安装 **Blender 4.5**（或兼容版本，默认路径通常为 `C:\Program Files\Blender Foundation\Blender 4.5\blender.exe`）。
* 系统中已安装 Anaconda 或 Miniconda。

#### 部署步骤

1. **创建 Conda 环境**
   创建名为 `building` 的 Python 3.10 运行环境：
   ```bash
   conda create -n building python=3.10 -y
   ```

2. **激活环境**
   ```bash
   conda activate building
   ```

3. **安装依赖包**
   进入项目根目录安装 Python 相关依赖：
   ```bash
   pip install -r requirements.txt
   ```

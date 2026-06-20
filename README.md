# Seismic Structural Simulation & Scene Builder / 抗震结构动力学仿真与场景构建工具

Bilingual: [English](#english) | [中文](#中文)

---

## English

### Project Purpose & Background
This project is an automated 3D physics simulation engine designed to study the structural deformation, brick-sliding (sag), and collapse behaviors of masonry walls under seismic loading. It is built entirely on Blender's 3D engine, utilizing rigid body physics, multi-body constraints, shape key animations, and procedural mesh generation.

#### Technical Pipeline
1. **Concrete Frame Generation** (`scripts/build_scene_*.py`): Procedurally builds structural concrete foundations, columns, and beams. Configures Hermite smoothstep shape keys (`Sway_X`, `Sway_Y`) to simulate elastic structural swaying.
2. **Masonry Wall Assembly**: Lays brick-by-layer wall arrays (alternating full and half-brick layouts) with micro-gaps to avoid initial physical penetrations.
3. **Cohesive Constraints**: Sets up Generic 6-DOF constraints between adjacent bricks and kinematic anchors to simulate plastic-like material properties (e.g. wall shear deformation, vertical sag sinking, and out-of-plane bowing).
4. **Earthquake Simulation**: Animates seismic shape key values, kinematic anchors, and oscillates the gravity vector ($G_z$) to replicate vertical earthquake accelerations (P-waves).
5. **DIC Dataset Camera Array**: Sets up a stereoscopic camera array (Front L/R, Right L/R) targeting the wall panels to capture high-resolution imagery for Digital Image Correlation (DIC) displacement tracking.

---

### Manual Deployment & Execution

#### Prerequisites
* **Blender 3.6** (or compatible version) installed globally on your system (typically in `C:\Program Files\Blender Foundation\Blender 3.6\blender.exe`).
* **Conda Environment**: Although the scripts use Blender's internal Python API (`bpy` and `bmesh`), a Conda environment `building` (Python 3.10) can be configured for auxiliary scripts and automation utilities.

#### Step-by-Step Execution

1. **Activate Conda Environment (Optional)**
   ```bash
   conda activate building
   ```

2. **Execute Script via Blender CLI**
   Because the main scripts rely on Blender's internal modules (`bpy`, `bmesh`), they must be executed through the Blender command-line interface. Run the following command in your terminal (adjusting the Blender executable path if necessary):
   ```bash
   & "C:\Program Files\Blender Foundation\Blender 3.6\blender.exe" --background --python scripts/build_scene_large_plastic_v4.py
   ```
   *Note: On Windows PowerShell, the `&` call operator is used to invoke paths containing spaces.*

3. **Output Results**
   Upon completion, the script will:
   * Procedurally build the frame, walls, cameras, and sun light.
   * Keyframe the structural swaying and seismic gravity.
   * **Bake the physics simulation** for frames 1-250.
   * Save the final baked scene to `E:\Antigravity\Building\anti_seismic_sim_large_plastic_v4.blend`.

---

## 中文

### 项目目的与背景
本项目是一个自动化的三维物理动力学仿真引擎，旨在研究砌体砖墙在地震荷载下的结构变形、滑移（下沉）以及倒塌失效行为。该工具完全基于 Blender 的三维引擎构建，集成了刚体动力学、多体约束、形态键（Shape Key）动画以及程序化网格生成算法。

#### 技术管线
1. **混凝土框架生成** (`scripts/build_scene_*.py`): 程序化生成基础、框架柱和框架梁。配置 Hermite 平滑插值的形态键（`Sway_X`、`Sway_Y`）来模拟建筑结构在地震中的弹性侧摆变形。
2. **砌体墙装配**: 自动交替铺设整砖与半砖的墙体阵列，并在砖缝间预留微小间隙以防止物理碰撞体初始穿模爆炸。
3. **粘结约束网络**: 在相邻砖块之间以及砖块与动力学锚点（Anchors）之间建立通用的六自由度（6-DOF）弹簧约束，以模拟墙体的塑性剪切变形、垂直下沉（Sag）以及出平面鼓出（Bowing）等力学特征。
4. **地震动模拟**: 动画化控制摆动形态键与动力学锚点位移，并对重力加速度 $G_z$ 施加高频简谐振荡以模拟地震垂直加速度（P波）。
5. **DIC 相机阵列**: 针对正面和侧面墙板架设了双目相机阵列（Front L/R，Right L/R），用于输出可供数字图像相关法（DIC）进行三维位移场跟踪的高清渲染图像序列。

---

### 使用 Conda 与 Blender 手动部署运行

#### 前提条件
* 系统中已全局安装 **Blender 3.6**（或兼容版本，默认路径通常为 `C:\Program Files\Blender Foundation\Blender 3.6\blender.exe`）。
* **Conda 环境**：尽管核心脚本依赖 Blender 内部的 Python API（`bpy` 和 `bmesh`），你依然可以配置 Conda 的 `building` 环境（Python 3.10）用于运行辅助脚本。

#### 运行步骤

1. **激活辅助环境（可选）**
   ```bash
   conda activate building
   ```

2. **通过 Blender 命令行执行仿真脚本**
   由于仿真脚本必须在 Blender 进程内调用其内置模块才能运行，因此需要通过命令行启动 Blender 来加载执行。请在终端执行以下命令（可根据实际安装路径调整 Blender 路径）：
   ```bash
   & "C:\Program Files\Blender Foundation\Blender 3.6\blender.exe" --background --python scripts/build_scene_large_plastic_v4.py
   ```
   *注：在 Windows PowerShell 中，`&` 符号是调用含有空格路径的可执行文件的调用操作符。*

3. **输出结果说明**
   脚本运行完成后，将自动完成以下操作：
   * 自动生成混凝土框架、砌体墙、相机阵列和太阳光源。
   * 写入 1-250 帧的地震侧摆位移与重力振荡关键帧。
   * **自动解算并烘焙（Bake）** 250 帧的刚体物理仿真。
   * 将最终的烘焙场景保存为本地 Blender 文件：`E:\Antigravity\Building\anti_seismic_sim_large_plastic_v4.blend`。

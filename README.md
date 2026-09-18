<div align="center">

# 🧠 CouncilLLM

### **An Offline Multi-Model AI Council**

**Multiple models. Specialized roles. One local intelligence layer.**

<br>

<p>
  <img src="assets/councillm-demo.gif" alt="CouncilLLM Demo" width="900">
</p>

<br>

<p>
  <img src="https://img.shields.io/badge/AI-Local-6C63FF?style=for-the-badge" alt="Local AI">
  <img src="https://img.shields.io/badge/Inference-Offline-00A67E?style=for-the-badge" alt="Offline Inference">
  <img src="https://img.shields.io/badge/Architecture-Multi--Model-5B8DEF?style=for-the-badge" alt="Multi-Model">
  <img src="https://img.shields.io/badge/Status-Active-F59E0B?style=for-the-badge" alt="Project Status">
</p>

<br>

[**Features**](#-features) ·
[**Architecture**](#-architecture) ·
[**Models**](#-the-model-council) ·
[**Installation**](#-installation) ·
[**Roadmap**](#-roadmap)

</div>

---

## 🧠 What is CouncilLLM?

**CouncilLLM** is an offline, multi-model AI system built around the concept of an **AI council**.

Instead of asking one model to handle every type of task, CouncilLLM gives different locally running models **specific responsibilities**.

Each model contributes according to its assigned role, while the CouncilLLM orchestration layer manages the overall interaction.

The result is a modular AI environment where **different models can work together without making a cloud AI service the foundation of the system.**

---

## ✦ The Idea

> ### **One model doesn't have to do everything.**

CouncilLLM treats AI models as members of a council.

Each member has a role.

```text
                         ┌─────────────────────┐
                         │      USER QUERY     │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │     COUNCILLM       │
                         │    ORCHESTRATOR     │
                         └──────────┬──────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
                    ▼               ▼               ▼
             ┌────────────┐  ┌────────────┐  ┌────────────┐
             │ 🧠 QWEN    │  │ 💻 GRANITE │  │ 👁 VISION  │
             │  Reasoning │  │   Coding   │  │   Visual   │
             └─────┬──────┘  └─────┬──────┘  └─────┬──────┘
                   │               │               │
                   └───────────────┼───────────────┘
                                   │
                                   ▼
                         ┌─────────────────────┐
                         │   COUNCIL OUTPUT    │
                         └─────────────────────┘
```

The architecture is intentionally **role-oriented**.

A coding model is used for coding.

A vision model is used for visual understanding.

A general reasoning model handles general interaction and reasoning.

---

# ✨ Features

<table>
<tr>
<td width="50%">

### 🧠 Multi-Model Intelligence

Run multiple local models as part of a single AI system.

</td>
<td width="50%">

### 🎯 Role-Based Models

Give each model a defined responsibility instead of treating every model identically.

</td>
</tr>

<tr>
<td>

### 💻 Local Coding

**Granite** is dedicated to coding and programming-oriented tasks.

</td>
<td>

### 👁️ Visual Understanding

A dedicated vision model handles visual tasks.

</td>
</tr>

<tr>
<td>

### 🔒 Privacy-Oriented

Designed around keeping the AI workflow within the local environment.

</td>
<td>

### 🧩 Modular Architecture

Models and system components can evolve independently.

</td>
</tr>

<tr>
<td>

### 🏠 Offline-First

The architecture is designed for local model execution without requiring cloud inference as its foundation.

</td>
<td>

### ⚙️ Local Control

Models, orchestration, and application components remain under the user's local environment.

</td>
</tr>
</table>

---

# 🏛️ Architecture

CouncilLLM is organized around several logical layers.

```text
┌──────────────────────────────────────────────────────────┐
│                         USER                             │
└────────────────────────────┬─────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────┐
│                       FRONTEND                           │
│                  User Interaction Layer                  │
└────────────────────────────┬─────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────┐
│                    COUNCILLM CORE                        │
│                                                          │
│                 Orchestration / Routing                  │
└───────────────────────┬───────────────┬──────────────────┘
                        │               │
              ┌─────────┘               └─────────┐
              ▼                                   ▼
┌─────────────────────────┐           ┌─────────────────────────┐
│      LOCAL MODELS       │           │      LOCAL SERVICES     │
│                         │           │                         │
│  🧠 Qwen                │           │  Authentication         │
│  💻 Granite             │           │  Configuration           │
│  👁 Vision              │           │  Application Logic      │
│  + Future Models        │           │  Other Components       │
└────────────┬────────────┘           └────────────┬────────────┘
             │                                     │
             └──────────────────┬──────────────────┘
                                ▼
                    ┌─────────────────────────┐
                    │      COUNCIL OUTPUT     │
                    └─────────────────────────┘
```

### 🔄 Request Flow

A simplified request lifecycle:

```text
        USER
         │
         ▼
    ┌──────────┐
    │  Query   │
    └────┬─────┘
         │
         ▼
 ┌─────────────────┐
 │   Orchestrator  │
 └────────┬────────┘
          │
     ┌────┼────┐
     │    │    │
     ▼    ▼    ▼
    🧠   💻   👁
   Qwen Granite Vision
     │    │    │
     └────┼────┘
          │
          ▼
   ┌──────────────┐
   │    Council   │
   │   Processing │
   └──────┬───────┘
          │
          ▼
    Final Response
```

---

# 🤖 The Model Council

CouncilLLM currently assigns models according to their intended responsibilities.

| Model                |    Role   | Primary Responsibility                       |
| :------------------- | :-------: | :------------------------------------------- |
| 🧠 **Qwen**          | Reasoning | General-purpose reasoning and interaction    |
| 💻 **Granite**       |   Coding  | Programming and coding tasks                 |
| 👁️ **Vision Model** |   Vision  | Visual understanding and image-related tasks |

### Why specialization?

The council does not need every model to perform every job.

Instead, each model can focus on the type of work it has been assigned.

```text
                    COUNCILLM
                        │
       ┌────────────────┼────────────────┐
       │                │                │
       ▼                ▼                ▼
    🧠 REASONING      💻 CODING       👁️ VISION
       │                │                │
      QWEN           GRANITE        VISION MODEL
```

This also makes the architecture easier to extend.

A future model can be introduced as another council member without requiring the entire system to be redesigned.

---

# 🔒 Offline by Design

CouncilLLM is built around a **local-first and air-gapped architecture**.

The intended environment looks like:

```text
┌──────────────────────────────────────────────┐
│                LOCAL MACHINE                 │
│                                              │
│   ┌──────────────────────────────────────┐   │
│   │             CouncilLLM               │   │
│   │                                      │   │
│   │     Frontend                         │   │
│   │        │                             │   │
│   │        ▼                             │   │
│   │     Backend                          │   │
│   │        │                             │   │
│   │        ▼                             │   │
│   │   ┌──────────────────────────────┐   │   │
│   │   │       Local Model Layer      │   │   │
│   │   │                              │   │   │
│   │   │   Qwen · Granite · Vision   │   │   │
│   │   └──────────────────────────────┘   │   │
│   │                                      │   │
│   └──────────────────────────────────────┘   │
│                                              │
└──────────────────────────────────────────────┘
```

### 🔐 Local-first principles

* 🏠 Local model execution
* 🔒 Privacy-oriented architecture
* 🌐 No cloud inference dependency at the core
* 🧩 Modular local components
* 👤 Local authentication
* 💾 Local data and configuration

---

# 👤 Local Authentication

CouncilLLM includes a local authentication concept designed specifically for its offline environment.

The system is built around:

| Component                       | Purpose                |
| :------------------------------ | :--------------------- |
| 👤 **Username**                 | Local account identity |
| 🔑 **Password**                 | Account authentication |
| 🧾 **Recovery Code**            | Account recovery       |
| 💻 **One Device / One Account** | Local account model    |

Account recovery uses a **generated recovery code** rather than security questions.

The authentication system is intended to operate locally without depending on an external identity provider.

---

# 🎬 CouncilLLM in Action

<p align="center">
  <img src="assets/councillm-demo.gif" alt="CouncilLLM running locally" width="900">
</p>

<p align="center">
  <sub>Example CouncilLLM workflow</sub>
</p>

<br>

### ▶️ Full Demonstration

For a longer demonstration, use the video thumbnail below:

<p align="center">
  <a href="YOUR_VIDEO_LINK">
    <img src="assets/demo-thumbnail.png" alt="Watch CouncilLLM Demo" width="800">
  </a>
</p>

<p align="center">
  <sub>Click to watch the full demonstration</sub>
</p>

---

# 🖥️ Interface

## Main Interface

<p align="center">
  <img src="assets/screenshots/main-interface.png" alt="CouncilLLM Main Interface" width="900">
</p>

## Council Processing

<p align="center">
  <img src="assets/screenshots/council-processing.png" alt="CouncilLLM Council Processing" width="900">
</p>

## Model Interaction

<p align="center">
  <img src="assets/screenshots/model-interaction.png" alt="CouncilLLM Model Interaction" width="900">
</p>

---

# ⚙️ How CouncilLLM Works

At a high level:

### 01 · 📝 User Input

The user provides a request through the local interface.

### 02 · 🧭 Orchestration

CouncilLLM determines how the request should be handled.

### 03 · 🤖 Model Participation

The appropriate local model or models perform their assigned tasks.

### 04 · 🏛️ Council Processing

The outputs are processed within the council workflow.

### 05 · 💬 Response

The resulting output is presented back to the user.

```text
┌──────────┐
│   USER   │
└────┬─────┘
     │
     ▼
┌───────────────┐
│   COUNCILLM   │
│ Orchestration │
└───────┬───────┘
        │
        ▼
┌──────────────────────────┐
│      MODEL COUNCIL       │
│                          │
│ 🧠 Qwen                  │
│ 💻 Granite               │
│ 👁️ Vision                │
└────────────┬─────────────┘
             │
             ▼
      ┌──────────────┐
      │   COUNCIL    │
      │   OUTPUT     │
      └──────┬───────┘
             │
             ▼
        ┌─────────┐
        │ RESPONSE│
        └─────────┘
```

---

# 🧩 Project Structure

The project follows a modular structure so that the interface, backend, orchestration logic, and model layer can evolve independently.

```text
CouncilLLM/
│
├── frontend/
│   └── ...
│
├── backend/
│   ├── council/
│   ├── models/
│   └── ...
│
├── assets/
│   ├── screenshots/
│   ├── councillm-demo.gif
│   ├── architecture.png
│   └── demo-thumbnail.png
│
├── config/
│   └── ...
│
├── README.md
└── ...
```

> **Note:** Update this tree to match the final repository structure before publishing.

---

# 🚀 Installation

## Requirements

CouncilLLM is designed to run on a machine capable of running the selected local models.

Requirements depend on:

* Model size
* Quantization
* Context length
* Number of models loaded
* Available RAM
* Available storage
* Local inference runtime

## Clone

```bash
git clone YOUR_REPOSITORY_URL
cd CouncilLLM
```

## Install Dependencies

```bash
YOUR_INSTALL_COMMAND
```

## Run

```bash
YOUR_RUN_COMMAND
```

> Replace the placeholder commands above with the actual project commands before publishing.

---

# ⚙️ Configuration

CouncilLLM is designed around configurable model roles.

A model configuration can conceptually contain:

```text
Model
├── Name
├── Role
├── Local Runtime / Endpoint
└── Task Type
```

This makes it possible to modify the council as the project grows.

---

# 🗺️ Roadmap

CouncilLLM is an evolving project.

### Foundation

* [x] 🧠 Local multi-model architecture
* [x] 🎯 Model-specific responsibilities
* [x] 🏠 Local model execution
* [x] 🖥️ Local frontend/backend architecture
* [x] 👤 Local authentication concept
* [x] 🧾 Recovery-code based account recovery

### Next

* [ ] 🏛️ Improve council orchestration
* [ ] 🔄 Improve response synthesis
* [ ] 🤖 Expand supported model roles
* [ ] 👁️ Expand visual capabilities
* [ ] ⚙️ Improve model configuration
* [ ] 🧪 Expand testing
* [ ] 📚 Expand documentation
* [ ] 🎨 Refine the user interface

---

# 🎯 Design Philosophy

CouncilLLM is built around five principles.

### 🏠 Local First

Keep the core AI workflow local.

### 🎯 Specialized Intelligence

Let models focus on the tasks they are assigned to handle.

### 🧩 Modularity

Keep individual components replaceable and extensible.

### 🔒 User Control

Keep the local AI environment under the user's control.

### ⚡ Practicality

Multiple models should serve a purpose, not exist merely because the architecture looks impressive on a diagram.

---

# 🛠️ Technology

CouncilLLM combines:

| Layer                 | Purpose                                  |
| :-------------------- | :--------------------------------------- |
| 🖥️ **Frontend**      | User interaction                         |
| ⚙️ **Backend**        | Application and orchestration logic      |
| 🧠 **Local LLMs**     | Language reasoning                       |
| 👁️ **Vision Model**  | Visual understanding                     |
| 💻 **Granite**        | Coding tasks                             |
| 🗃️ **Local Storage** | Local application data and configuration |

> Add the exact frameworks, runtimes, libraries, and versions here as the implementation stabilizes.

---

# 🤝 Contributing

Contributions are welcome.

If you'd like to contribute:

```text
1. Fork the repository
       ↓
2. Create a branch
       ↓
3. Make your changes
       ↓
4. Test locally
       ↓
5. Open a pull request
```

For larger architectural changes, please explain the reasoning behind the change and how it fits into the existing council architecture.

---

# 📜 License

This project is licensed under the **[LICENSE NAME]** License.

See [`LICENSE`](LICENSE) for details.

---

# 🙏 Acknowledgements

CouncilLLM builds upon the broader ecosystem of open-source AI models and local inference technologies.

Individual model licenses and terms remain applicable to the models used with CouncilLLM.

---

<div align="center">

## 🧠 CouncilLLM

**Multiple models. Specialized roles. One local council.**

<br>

<img src="assets/councillm-logo.png" alt="CouncilLLM" width="100">

<br><br>

<sub>Built for local AI experimentation, orchestration, and research.</sub>

</div>

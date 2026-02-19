# Safe-Edge Blackbox 🛡️📦
### Smart Factory 3-Node HA Edge Orchestration & Data Preservation System

> **스마트 팩토리 환경을 위한 3-Node 고가용성(HA) 엣지 오케스트레이션 및 데이터 보존 시스템**

## 📖 Project Overview (프로젝트 개요)

### 🚨 Problem: The Blackout
산업 현장에서 화재나 폭발 사고 발생 시, 현장의 감시 장비가 파손되면 내부 데이터(SD카드 등)도 함께 소실되어 원인 규명이 불가능한 **'Blackout'** 현상이 발생합니다.

### 💡 Solution
본 프로젝트는 'Control Plane(지휘)'과 'Data Plane(현장)'을 물리적으로 분리하고, 사고 직전의 데이터를 안전 구역으로 실시간 복제하는 고가용성 아키텍처를 구현합니다.

**핵심 목표:**
1.  **Control Plane 격리:** 마스터 노드를 연산에서 배제하여 클러스터의 생존성을 극대화합니다.
2.  **무중단 Failover:** 위험 구역 노드(W2) 파괴 시, 안전 구역 대기 노드(W1)가 즉시 임무를 승계합니다.
3.  **데이터 이원화:** SSD(Hot)와 NFS(Cold)를 결합한 하이브리드 저장소를 구축합니다.
4.  
---

## 🏆 Main Contributions (주요 기여 및 기대 효과)

본 프로젝트는 기존 산업용 엣지 시스템의 한계를 극복하고, 재난 상황에서도 데이터의 무결성을 보장하는 새로운 아키텍처를 제안합니다.

### 1. Zero-Loss Data Architecture for Edge (데이터 무손실 아키텍처)
* **기존 문제:** 엣지 디바이스는 저장 공간이 부족하고, 물리적 충격에 취약하여 사고 시 데이터가 소실(Blackout)되는 치명적인 단점이 있었습니다.
* **본 프로젝트의 기여:**
    * **이중화 스토리지 (Tiering Strategy):** `Longhorn`의 동기식 복제(Synchronous Replication)를 통해 위험 구역(Danger Zone)의 데이터를 안전 구역(Safe Zone)으로 실시간 미러링하여 **RPO(목표 복구 시점) 0초**를 달성했습니다.
    * **하이브리드 보존:** 엣지의 SSD(Hot Data)와 온프레미스 서버의 HDD(Cold Data)를 결합하여, 엣지 디바이스의 제한된 용량 문제를 해결함과 동시에 데이터 보존 기간을 비약적으로 늘렸습니다.

### 2. High-Availability Edge Orchestration (고가용성 엣지 오케스트레이션)
* **기존 문제:** 단일 노드 시스템은 하드웨어 고장 시 전체 감시 시스템이 마비되는 단일 실패 지점(SPOF) 문제가 존재했습니다.
* **본 프로젝트의 기여:**
    * **Control Plane 격리:** 리소스가 부족한 엣지 환경(Pi 5 4GB)에서도 `Taint` 설정을 통해 마스터 노드의 부하를 원천 차단하여 클러스터 안정성을 확보했습니다.
    * **초고속 Failover:** `Kubernetes`의 파드 스케줄링 전략(Affinity/Toleration)을 최적화하여, 물리적 파괴 상황에서도 **1분 이내(Target RTO)**에 대기 노드(Worker 1)가 임무를 자동 승계하는 무중단 감시 체계를 구현했습니다.

### 3. Cost-Effective Disaster Recovery System (저비용 고효율 DR 시스템)
* **기존 문제:** 기존의 고가용성 솔루션(HACMP 등)은 고가의 서버와 라이선스 비용이 필요하여 중소규모 스마트 팩토리에 도입하기 어려웠습니다.
* **본 프로젝트의 기여:**
    * **오픈 소스 기반:** `K3s`, `ArgoCD`, `Grafana` 등 100% 오픈 소스 기술 스택을 활용하여 라이선스 비용을 제거했습니다.
    * **경량 하드웨어 활용:** 범용 SBC(Single Board Computer)인 라즈베리파이를 클러스터링하여, 고가의 산업용 서버 대비 **90% 이상의 비용 절감 효과**를 입증했습니다.

---

## 🏗️ Hardware Architecture (하드웨어 구성)

시스템은 물리적으로 **Safe Zone, Buffer Zone, Danger Zone**의 3계층으로 구성되며, 각 노드는 Layer 2 Switch로 연결됩니다.

![Hardware Architecture](hardware_edit.jpg)

| Role | Hostname (IP) | Zone | Mission & Specs |
| :--- | :--- | :--- | :--- |
| **Control Plane** | `Master` (192.168.0.10) | **Safe Zone**<br>(관제실) | • **Role:** Cluster Orchestration & Monitoring<br>• **Components:** Battery, Board, Monitor<br>• **Spec:** Pi 5 (4GB) |
| **Standby Worker** | `Worker 1` (192.168.0.11) | **Buffer Zone**<br>(안전 펜스/경계) | • **Role:** Hot Standby & Buffer<br>• **Components:** Battery, Board, Camera, Audio, Temp Sensor<br>• **Spec:** Pi 5 (8GB) |
| **Active Worker** | `Worker 2` (192.168.0.12) | **Danger Zone**<br>(현장/사고 위험) | • **Role:** Main Sensing & AI Processing<br>• **Components:** Battery, Board, Camera, Audio, Temp Sensor<br>• **Spec:** Pi 5 (8GB) |

---

## ⚙️ System & Network Infrastructure (시스템 아키텍처)

외부 PC(Host)와 K3s 클러스터 간의 유기적인 연결을 통해 DevOps 파이프라인과 모니터링 시스템을 구축했습니다.

![Infrastructure Diagram](infra_edit.jpg)

### 1. External Access (Host PC)
* **IP:** 192.168.0.100
* **Role:**
    * **GitLab:** 소스코드 형상 관리 및 CI/CD 트리거
    * **Ansible:** 인프라 자동화 및 설정 관리
    * **NFS Server:** Cold Data(장기 보관 데이터) 저장소

### 2. K3s Cluster
* **Load Balancer:** MetalLB를 통한 외부 접속 관리
* **Ingress:** Traefik
* **CD:** ArgoCD를 통한 GitOps 배포 자동화
* **Storage:** Longhorn (분산 블록 스토리지)

### 3. Data Flow
* **Hot Data:** `Worker 2` → `Longhorn` (Real-time Replication to `Worker 1`)
* **Cold Data:** `Worker 1` → `Host PC NFS` (Scheduled Backup)
* **Metrics:** `Sensors` → `InfluxDB` → `Grafana`

---

## 🚀 Key Implementation Tasks (주요 구현 내용)

프로젝트는 다음의 핵심 작업 흐름을 통해 단계적으로 구축되었습니다.

### 1️⃣ Foundation & Network Setup (기초 공사)
* **Node Setup:** 라즈베리파이 OS 설치, 고정 IP 설정 및 호스트네임 변경.
* **Network Optimization:** SSH 접속 환경 구성 및 대용량 데이터 전송을 위한 **MTU 9000** 설정.
* **PC Server:** Docker 기반의 GitLab 및 Grafana 컨테이너 실행, NFS 서버 공유 폴더 권한 설정.

### 2️⃣ Cluster & Storage Construction (클러스터 구축)
* **K3s Init:** Master 노드 서버 구축 및 Taint(스케줄링 방지) 설정.
* **Node Join:** Worker 1, 2 노드 클러스터 연결 및 상태 확인 (`kubectl get nodes`).
* **Storage:** Longhorn 설치 및 웹 대시보드 연동, 각 노드에서 PC의 NFS 폴더 마운트 테스트.
* **Volume:** 테스트용 PV/PVC 생성 및 파드 연결 검증.

### 3️⃣ Edge AI & Hardware Integration (AI/하드웨어)
* **Hardware Check:** 카메라(`/dev/video0`) 및 마이크 장치 정상 인식 확인.
* **AI Container:** Docker 환경에서 YOLO(Vision) 및 YAMNet(Audio) 컨테이너 단독 실행 테스트.
* **Data Collection:** 컨테이너 내부에서 영상/음성 데이터가 정상적으로 수집되는지 검증.

### 4️⃣ DevOps & Monitoring (운영 환경)
* **GitOps:** ArgoCD 설치 및 CLI 로그인, GitLab 리포지토리 연동.
* **Auto Sync:** Hello World 앱 배포를 통해 Git Push 시 자동 동기화 확인.
* **Monitoring Stack:** 클러스터 내부에 Prometheus/InfluxDB 설치 및 NodePort 개방.
* **Visualization:** PC의 Grafana에서 K3s 데이터 소스 연결 및 노드 상태(CPU, 온도) 대시보드 패널 생성.

### 5️⃣ Failover & Data Strategy (고가용성 구현)
* **Affinity & Toleration:**
    * 평시에는 `Worker 2`에 파드가 배치되도록 `Node Affinity` 설정.
    * 비상시 `Worker 1`이 즉시 승계할 수 있도록 `Toleration` 설정.
* **Data Logic:**
    * **Hot Data:** 실시간 SSD 저장 로직 구현 (Longhorn).
    * **Cold Data:** 주기적으로 NFS로 이관하는 백업 사이드카(Sidecar) 컨테이너 구현.
* **Crash Test (Simulation):**
    * **Scenario:** `Worker 2` 랜선 제거(폭발 시뮬레이션).
    * **Verification:** `Worker 1`에서 1분 이내 파드 자동 재기동 확인 및 사고 직전 데이터(Hot Data) 보존 여부 검증.

### 6️⃣ Optimization & Finalization (최적화)
* **Backup Verification:** Failover 후 남은 데이터가 PC NFS로 정상 백업되는지 확인.
* **Tuning:** Failover 시간 단축을 위한 파라미터 튜닝.
* **Documentation:** 소스 코드 주석 작성, 트러블 슈팅 문서화 및 최종 보고서 작성.

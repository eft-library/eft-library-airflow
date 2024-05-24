# [Airflow] Airflow 2.9.1 설치

> Airflow 2.9.1 및 Python 3.9를 설치하는 방법 입니다.

> Rocky linux 8 환경이며, 패키지가 아무것도 깔려있지 않은 깡통 환경에서 구축 입니다. - ps, clear 등 안됨

# Airflow 구축

## 패키지 설치

설치에 필요한 패키지와, 사용할 명령어들의 패키지를 설치 합니다.

```bash
# yum update
yum update -y

# 나머지 패키지 설치
yum install ncurses -y
yum install procps -y
yum install make -y
yum install gcc glibc glibc-common gd gd-devel -y
yum install openssl-devel -y
yum install libffi-devel -y
yum install wget -y
yum install findutils -y
yum install sqlite-devel -y
```

## Python 3.9 설치

wget을 사용하여 Python 3.9.19를 설치 합니다. 꼭 이 버전이 아니어도 가능하며 3.8 이상이면 됩니다.

```bash
# python 다운로드
wget https://www.python.org/ftp/python/3.9.19/Python-3.9.19.tgz
tar xvf Python-3.9.19.tgz
cd Python-3.9.19

# 최적화된 옵션으로 빌드 하면서 ssl 활성화
./configure --enable-optimizations --with-ssl

# make install
make
make install

# pip 업그레이드
/usr/local/bin/python3.9 -m pip install
pip3 install --upgrade pip
```

## Airflow 설치

```bash
# 가상환경 생성 및 적용
python3.9 -m venv airflow_venv
source airflow_venv/bin/activate

# pip 업그레이드
pip install --upgrade pip

# 환경 변수 설정 
export AIRFLOW_HOME=/volume1/tkw/airflow
export AIRFLOW_VERSION=2.9.1

# 아래의 내용은 그냥 명시적으로 적어도 됩니다. ex) export PYTHON_VERSION=3.9
export PYTHON_VERSION="$(python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
export CONSTRAINT_URL="https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-${PYTHON_VERSION}.txt"

# Airflow 설치
pip install "apache-airflow==${AIRFLOW_VERSION}" --constraint "${CONSTRAINT_URL}"

# 사용할 DB에 맞는 driver 설치 - 여기서는 postgresql을 사용
pip install psycopg2-binary

# postgresql connection
pip install apache-airflow-providers-postgres
```

## Airflow 환경 설정

초기에 설정 파일을 얻기 위해 airflow db migrate를 진행한 뒤, 설정을 바꾼 후 다시 migrate를 진행합니다.

```bash
# 초기 migrate
airflow db migrate

# 필요 없는 db 정보 제거
rm -f airflow.db

# 생성된 config 파일 수정
vi airflow.cfg

# timezone
default_timezone = Asia/Seoul

# 동시에 실행할 수 있는 최대 task - 서버 환경에 맞춰서 사용하면 됩니다. 
parallelism = 8

# web port - 사용할 port를 사용하면 됩니다.
web_server_port = 13000

# 기본은 SequentialExecutor 이며 단일 스레드 입니다. 병렬처리를 할 수 없으니, LocalExecutor로 변경해줍니다. - 별도의 DB가 연결되어야 합니다.
executor = LocalExecutor

# 예시 파일 없음
load_examples = False

# DB 연결 - postgresql
sql_alchemy_conn = postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}

# 위의 내용을 수정하여 저장하였으면 적용을 위해 migrate 해줍니다.
airflow db migrate

# airflow에 Admin Role을 가진 계정을 추가합니다.
airflow users create --username {user} --firstname {firstname} --lastname {lastname} --role Admin --email {email}
```

## Airflow 실행 및 확인
```bash
# webserver 실행 및 확인
nohup airflow webserver > webserver.log 2>&1 &
tail -f webserver.log

# scheduler 실행 및 확인
nohup airflow scheduler > scheduler.log 2>&1 &
tail -f webserver.log
```

잘 접속 되면 설정한 Port로 접속하면 됩니다.

# Trouble Shooting

> 설치를 진행하며 발생한 문제 입니다.

## Docker 환경에서의 문제

Docker 컨테이너에서 구축했을 경우, bash로 재접속 하면 환경 변수가 사라지는 문제가 있습니다. Container의 정상적인 동작이며 저희가 해결해야 합니다.

위에서 export 하는 변수들을 container를 구축할 때 정해야 합니다. 이 방식은 airflow와 python의 버전을 특정했을때 사용가능합니다.

    예시1) 
    docker run -e AIRFLOW_HOME=/home/airflow -e AIRFLOW_VERSION=2.9.1 -e PYTHON_VERSION=3.9 -e CONSTRAINT_URL="https://raw.githubusercontent.com/apache/airflow/constraints-2.9.1/constraints-3.9.txt"

```
예시 2)
services:
  my_service:
    image: my_image
    environment:
      AIRFLOW_HOME=/home/airflow  
      AIRFLOW_VERSION=2.9.1  
      PYTHON_VERSION=3.9  
      CONSTRAINT_URL="https://raw.githubusercontent.com/apache/airflow/constraints-2.9.1/constraints-3.9.txt"
```

## 네트워크 속도

webserver.log 를 모니터링 해보면, 사용자가 접속했을때 js와 css등을 cdn을 통해 api로 가져옵니다.

제가 구축한 서버는 속도가 매우 느렸는데, 네트워크에 오버헤드가 커서 느렸습니다.

docker, local 둘 다 설치해 보았는데, 집에 인터넷이 느려서 안되는 거 같습니다.

이사를 간 뒤, 인터넷을 바꿔 해결해야 할 것 같습니다.



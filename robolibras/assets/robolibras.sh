#!/bin/bash

# RoboLibras — Instalador automático (Linux/macOS)

set -e

REPO_URL="https://github.com/ianderichalski/robo-libras.git"
REPO_DIR="robo-libras"
MODEL_URL="https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"

echo ""
echo "  RoboLibras — Instalador automático"
echo "  Objeto de Aprendizagem para o Ensino do Alfabeto Manual da LIBRAS"
echo "  -------------------------------------------------------------------"
echo ""

OS="$(uname -s)"

# Python 3.10
echo "[1/7] Verificando Python 3.10..."
if command -v python3.10 &>/dev/null; then
    echo "      Python 3.10 encontrado!"
else
    echo "      Instalando Python 3.10..."
    if [ "$OS" = "Linux" ]; then
        sudo apt update -qq
        sudo add-apt-repository ppa:deadsnakes/ppa -y &>/dev/null
        sudo apt update -qq
        sudo apt install -y python3.10 python3.10-venv python3.10-dev
    elif [ "$OS" = "Darwin" ]; then
        command -v brew &>/dev/null || /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        brew install python@3.10
    fi
    echo "      Python 3.10 instalado!"
fi

# Git
echo ""
echo "[2/7] Verificando Git..."
if command -v git &>/dev/null; then
    echo "      Git encontrado!"
else
    echo "      Instalando Git..."
    [ "$OS" = "Linux" ] && sudo apt install -y git || brew install git
    echo "      Git instalado!"
fi

# Clonar repositório
echo ""
echo "[3/7] Baixando o RoboLibras..."
if [ -d "$REPO_DIR" ]; then
    echo "      Pasta já existe. Atualizando..."
    cd "$REPO_DIR" && git pull && cd ..
else
    git clone "$REPO_URL"
fi
echo "      Download concluído!"

# Ambiente virtual
echo ""
echo "[4/7] Criando ambiente virtual Python..."
cd "$REPO_DIR"
python3.10 -m venv venv
echo "      Ambiente virtual criado!"

# Dependências
echo ""
echo "[5/7] Instalando dependências (pode demorar alguns minutos)..."
source venv/bin/activate
pip install --upgrade pip --quiet
pip install streamlit mediapipe opencv-python numpy SpeechRecognition protobuf scikit-learn Pillow pyFirmata --quiet

echo "      Instalando PyAudio (modo voz)..."
if [ "$OS" = "Linux" ]; then
    sudo apt install -y portaudio19-dev python3-dev &>/dev/null
elif [ "$OS" = "Darwin" ]; then
    brew install portaudio &>/dev/null
fi
pip install pyaudio --quiet || echo "      Aviso: PyAudio não instalado. Modo voz indisponível."
echo "      Dependências instaladas!"

# Baixar modelo MediaPipe
echo ""
echo "[6/7] Baixando modelo de reconhecimento de gestos (~25MB)..."
mkdir -p models
if [ ! -f "models/hand_landmarker.task" ]; then
    curl -L "$MODEL_URL" -o models/hand_landmarker.task 2>/dev/null && \
        echo "      Modelo baixado!" || \
        echo "      Aviso: Falha ao baixar modelo. Será baixado automaticamente ao abrir a câmera."
else
    echo "      Modelo já existe!"
fi

# Script de inicialização
echo ""
echo "[7/7] Criando script de inicialização..."
cd ..
cat > iniciar_robolibras.sh << 'EOF'
#!/bin/bash
cd robo-libras
source venv/bin/activate
echo "Iniciando RoboLibras..."
echo "Acesse: http://localhost:8501"
streamlit run app.py
EOF
chmod +x iniciar_robolibras.sh
echo "      Script criado: iniciar_robolibras.sh"

echo ""
echo "  -------------------------------------------------------------------"
echo "  Instalação concluída com sucesso!"
echo ""
echo "  Para iniciar o RoboLibras nas próximas vezes:"
echo "    ./iniciar_robolibras.sh"
echo "    O navegador abrirá automaticamente em: http://localhost:8501"
echo ""
echo "  Para uso completo com hardware:"
echo "    - Conecte o Arduino com firmware StandardFirmata"
echo "    - Informe a porta serial na interface (ex: /dev/ttyUSB0)"
echo ""
echo "  Pressione Enter para iniciar agora ou Ctrl+C para sair..."
read

cd robo-libras
source venv/bin/activate
streamlit run app.py

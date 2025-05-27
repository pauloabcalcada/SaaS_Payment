#!/bin/bash

echo "🔄 Ativando suporte ao conda..."
source ~/opt/anaconda3/etc/profile.d/conda.sh

echo "🔧 Criando ambiente 'saas_pay' com Python 3.12..."
conda create -y -n saas_pay python=3.12

echo "✅ Ativando ambiente 'saas_pay'..."
conda activate saas_pay

echo "📂 Verificando se requirements.txt existe..."
if [ ! -f "requirements.txt" ]; then
    echo "❌ requirements.txt não encontrado! Abortando."
    exit 1
fi

echo "📦 Instalando pacotes do requirements.txt..."
pip install -r requirements.txt

echo "✅ Ambiente 'saas_pay' pronto para uso."
echo "ℹ️ Use 'conda activate saas_pay' para ativar o ambiente no futuro."

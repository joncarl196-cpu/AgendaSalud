@echo off
echo ================================================================
echo AgendaSalud - Dispensario La Dolorosa - Iniciando...
echo ================================================================
echo Verificando Python...
python --version
echo.
echo Instalando dependencias automaticamente...
python -m pip install --upgrade pip --quiet
python -m pip install tkcalendar --quiet
echo.
echo Ejecutando AgendaSalud...
echo.
python main.py
pause

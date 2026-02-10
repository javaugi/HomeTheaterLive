@echo off
echo Activating Conda...
call C:\ProgramData\anaconda3\Scripts\activate.bat

rem Deactivate the current env
conda deactivate
conda remove -n dev --all

echo Creating environment...
rem Create a clean environment with ONLY spyder and python
rem conda create -n dev python=3.11
conda create -n dev python=3.11 spyder -y

rem Activate it
echo Activating environment...
conda config --set auto_activate_base false
conda activate dev

echo Installing common packages...
rem pip install package_name - always install pip inside Conda env
rem pip install --upgrade ipython prompt_toolkit
rem sudo conda update -n base -c defaults conda
conda install numpy pandas matplotlib requests
conda install pyqt
conda install spyder-kernels

conda install --force-reinstall python
conda install --force-reinstall spyder
rem conda update spyder

conda --version
python --version
pip --version
where python
where spyder
where pip

rem Try to launch
spyder
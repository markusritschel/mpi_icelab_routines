# Routines for the MPIM Sea Ice Lab
This repository contains routines for several devices used in the sea ice laboratory of the Max-Planck-Insitute for Meteorology in Hamburg.
All the read-out routines return a  python object (mostly `pandas` or `xarray` ) which can be used for further processing.
Also, you can find an `icelab_environ.yaml` file to create a virtual environment with all the python dependencies needed for the routines here.

---

## Usage

Most of the routines have a CLI and further information on their usage can be obtained by calling the python script with `--help`.

## Categories

The routines are split into the following categories:

### CTDs

Once the data got uploaded to the computer, use this routine to process the data.
This will return a `pandas.DataFrame` with a DateTime index and the variables as column names.

### Salinity harps
This routine will process data logged by the salinity harps (developed by Leif Riemenschneider).
Data are first read into a `pandas.DataFrame` object and then converted into a `xarray.Dataset`.
Select a module number (harp identifier) and the program will calculate certain parameters for you, e.g.:
- Salinity of Brine
- Bulk Salinity
- Solid Fraction
- Liquid Fraction

and make them available in the dataset.
Users are able to select the method based on which the brine salinity is calculated (see the documentation for further help).


### Files created by the Arduino
For the master thesis of Markus Ritschel, an Arduino was installed to log data from various instruments, i.e. 
- Greisinger GMH 3700 thermometer
- Greisinger GMH 5550 pH meter
- Bosch BME 280 sensor (temeprature, relative humidity, pressure),
and to control either $\ce{CO2}$ content in the air or the pH value in the water.
You find both the data processing routine as well as the Arduino code in this repository.

This repository also ships with some basic plotting routines to graphically represent the respective data and some iPython notebooks with examples.
Some of the routines can make use of configuration specified in `config.yaml`.
Further information can be found in the docstrings of the respective methods and in the configuration file itself.

---

If you have any questions or concerns feel free to contact me via [email](mailto:git@markusritschel.de) or open an issue.

---

#### ToDos

- [ ] Add the option to group several harps (stacked underneath each other) to simulate “one” device.
- [ ] Extensive description/readme for the Arduino code
- [ ] Convert to package to make routines directly accessible in python

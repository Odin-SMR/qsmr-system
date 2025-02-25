restoredefaultpath

% qsmr_data dependencies
addpath('./qsmr/Mscripts_arts');
addpath("./qsmr/Mscripts_atmlab/");
addpath("./qsmr/Mscripts_atmlab/xml");
addpath("./qsmr/Mscripts_atmlab/time");
addpath("./qsmr/Mscripts_database/");
addpath("./qsmr/Mscripts_misc/");
addpath("./qsmr/Mscripts_qsystem/");
addpath("./qsmr/Mscripts_webapi/");
addpath("./qsmr-data/Mscripts_external/");
addpath("./qsmr-data/Mscripts_precalc/");
addpath("./qsmr-data/Mscripts_qsystem/");
addpath("./qsmr-data/Settings/");

% xml package uses eval to construct calls to read and write functions
xmlRead = dir("./qsmr/Mscripts_atmlab/xml/*Read*");
xmlWrite = dir("./qsmr/Mscripts_atmlab/xml/*Write*");
xmlFiles = "./qsmr/Mscripts_atmlab/xml/" + [string({xmlRead.name}), string({xmlWrite.name})];

% compile precalc
appFile = "precalc.m";
results = compiler.build.standaloneApplication(appFile, 'AdditionalFiles', xmlFiles);
compiler.runtime.customInstaller("precalcInstaller",results);

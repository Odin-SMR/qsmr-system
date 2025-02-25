restoredefaultpath

% qsmr dependencies
addpath(genpath('./qsmr/Mscripts_arts'));
addpath(genpath("./qsmr/Mscripts_atmlab/"));
addpath(genpath("./qsmr/Mscripts_database/"));
addpath(genpath("./qsmr/Mscripts_misc/"));
addpath(genpath("./qsmr/Mscripts_qsystem/"));
addpath(genpath("./qsmr/Mscripts_webapi/"));

% xml package uses eval to construct calls to read and write functions
xmlRead = dir("./qsmr/Mscripts_atmlab/xml/*Read*");
xmlWrite = dir("./qsmr/Mscripts_atmlab/xml/*Write*");
xmlFiles = "./qsmr/Mscripts_atmlab/xml/" + [string({xmlRead.name}), string({xmlWrite.name})];

% compile qsmr
appFile = "qsmr.m";
results = compiler.build.standaloneApplication(appFile, 'AdditionalFiles', xmlFiles);
compiler.runtime.customInstaller("qsmrInstaller",results);
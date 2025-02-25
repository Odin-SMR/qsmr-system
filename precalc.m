% Run precalc to generate abs lookup data for an invemode and freqmode.
function precalc(out_path, invemode, freqmode)
    freqmode = str2num(freqmode);
    fprintf('Using Q config with freqmode %d and invmode %s\n', ...
        freqmode, invemode);

    if invemode == "stnd"
        start_Q = q_stnd(freqmode);
    elseif invemode == "meso"
        start_Q = q_meso(freqmode);
    else
        error('not a valid invemode')
    end

    Q = q_versions(start_Q);

    if invemode == "meso"
        P = p_stnd(true);
    else
        P = p_stnd;
    end

    investr = Q.INVEMODE;
    investr(1) = upper(investr(1));
    investr(2:end) = lower(investr(2:end));

    datadir = '/QsmrData';

    % Fix paths
    %
    Q.ARTS = 'LD_LIBRARY_PATH="" /opt/bin/arts';
    Q.FOLDER_WORK = '/tmp';
    %
    Q.FOLDER_ABSLOOKUP = fullfile(out_path, 'AbsLookup', investr);
    Q.FOLDER_FGRID = fullfile(datadir, 'DataPrecalced', ...
        'Fgrid', investr);
    %
    inputfolder = fullfile(datadir, 'DataInput', 'Absorption');
    P.CONTINUA_FILE = fullfile(inputfolder, 'continua_std.arts');
    P.PARTITION_FILE = fullfile(inputfolder, 'tips.xml');
    P.SPECTRO_FILE = fullfile(inputfolder, 'smr_linedata.xml');

    % Paths not used for pre-calculations, but set here to have path settings
    % in one file
    Q.FOLDER_ANTENNA = fullfile(datadir, 'DataPrecalced', 'Antenna');
    Q.FOLDER_BACKEND = fullfile(datadir, 'DataPrecalced', 'Backend');

    % Save the Q to be used in the inversion
    save(fullfile(out_path, 'Q.mat'), 'Q');

    % Set some paths that should not be used for operational inversions
    Q.FOLDER_MSIS90 = fullfile(datadir, 'DataInput', 'Temperature');
    Q.FOLDER_BDX = fullfile(datadir, 'DataPrecalced', ...
        'SpeciesApriori', 'Bdx');

    % Calculate absorption table
    q2_precalc_abslookup(Q, P, '/tmp');

end

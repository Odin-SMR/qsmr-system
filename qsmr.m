% Run calculation and send results as json to an api if target_url
% is provided. If not, write results to .mat files.

function [] = qsmr()
    % Main loop: uses Python generator to get queue messages as JSON and process them
    [status, pyExe] = system("which python");
    if status ~= 0
        error("Python not found in PATH");
    end

    pyExe = strtrim(pyExe);
    pyenv( ...
        "Version", pyExe, ...
        "ExecutionMode", "OutOfProcess" ...
    );
    fprintf(string(py.sys.version) + "\n");
    fprintf(string(py.sys.executable) + "\n");

    msg_iter = py.qsmr_system.batch_qsmr.yield_queue_messages();

    while true
        try
            job = py.builtins.next(msg_iter);
        catch err
            fprintf('No more jobs or error: %s\n', err.message);
            pause(5);
            continue;
        end

        source_url = string(job.task.source);
        project = string(job.task.target);

        Q = load('/QsmrData/Q.mat');
        Q = Q.Q;

        LOG = webread_retry(source_url);

        if isempty(LOG)
            job.nack(0, "empty_log");
            fclose('all');
            continue;
        end

        try
            if Q.FREQMODE ~= LOG.FreqMode
                job.nack(0, "freqmode_mismatch");
                fclose('all');
                continue;
            end
        catch err
            job.nack(0, "LOG-file: error " + err.message);
            fclose('all');
            continue;
        end

        try
            L1B = get_scan_l1b_data(LOG.URLS.URL_spectra);
            [L2, L2I, L2C] = q2_inv(LOG, L1B, Q);

            data = struct('L2', L2, 'L2I', L2I, 'L2C', strjoin(L2C, newline));
            webwrite_retry(project, data);
            job.ack("success");
        catch err2
            job.nack(0, "processing_error: " + err2.message);
        end

        fclose('all');
    end

end

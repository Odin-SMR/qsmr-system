% Run calculation and send results as json to an api if target_url
% is provided. If not, write results to .mat files.
% example source url:
% http://malachite.rss.chalmers.se/rest_api/v4/freqmode_info/2015-04-01/AC2/1/7123991206/

function [] = qsmr()
    % Main loop: uses Python generator to get queue messages as JSON and process them
    ensurePythonVenv();
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

        try
            Q = load('/QsmrData/Q.mat');
            Q = Q.Q;
            fprintf('Using Q config with freqmode %d and invmode %s and backendfile %s\n', ...
                Q.FREQMODE, Q.INVEMODE, Q.BACKEND_FILE);

            max_retries = 5;
            LOG = webread_retry(source_url, weboptions('ContentType', 'json', ...
                'Timeout', 300), max_retries);

            if isempty(LOG)
                fprintf('Empty results from URL-input: %s\n', source_url);
                continue;
            end

            if Q.FREQMODE ~= LOG.FreqMode
                fprintf('Freqmode missmatch, Q: %d, LOG: %d\n', Q.FREQMODE, ...
                    LOG.Data.FreqMode);
                continue;
            end

            L1B = get_scan_l1b_data(LOG.URLS.URL_spectra);
            disp('Loaded L1B data');
            [L2, L2I, L2C] = q2_inv(LOG, L1B, Q);

            fprintf(strjoin(L2C, newline) + "\n");
            data = struct('L2', L2, 'L2I', L2I, 'L2C', strjoin(L2C, newline));
            webwrite_retry(project, data);
            job.ack();
        catch err2
            job.nack(60);
            fprintf('Error processing job: %s\n', err2.message);
        end

        fclose('all');
    end

end

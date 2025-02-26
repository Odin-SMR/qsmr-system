% Run calculation and send results as json to an api if target_url
% is provided. If not, write results to .mat files.
% example source url:
% http://malachite.rss.chalmers.se/rest_api/v4/freqmode_info/2015-04-01/AC2/1/7123991206/
function []=qsmr( source_url, target_url, target_username, target_password )

    Q = load('/QsmrData/Q.mat');
    Q = Q.Q;

    disp(sprintf( 'Using Q config with freqmode %d and invmode %s and backendfile %s', ...
                  Q.FREQMODE, Q.INVEMODE, Q.BACKEND_FILE))

    max_retries = 5;
    LOG = webread_retry(source_url, weboptions('ContentType', 'json', ...
        'Timeout', 300), max_retries);
    if isempty(LOG)
        disp(sprintf('Empty results from URL-input: %s', source_url));
        exit(2)
    end
    if Q.FREQMODE ~= LOG.Info.FreqMode
        disp(sprintf('Freqmode missmatch, Q: %d, LOG: %d', Q.FREQMODE, ...
                        LOG.Info.FreqMode))
        exit(1)
    end

    L1B = get_scan_l1b_data(LOG.Info.URLS.URL_spectra);

    [L2, L2I, L2C] = q2_inv(LOG.Info, L1B, Q);

    if nargin < 2
        save('L2.mat', 'L2');
        save('L2I.mat', 'L2I');
        save('L2C.mat', 'L2C');
    else
        if nargin < 3
            options = weboptions( ...
                'MediaType','application/json', ...
                'Timeout', 300);
        else
            options = weboptions( ...
                'MediaType','application/json', ...
                'Timeout', 300, ...
                'Username', target_username, ...
                'Password', target_password);
        end
        disp(strjoin(L2C, newline));
        data = struct('L2', L2, 'L2I', L2I, 'L2C', strjoin(L2C, '\n'));
        response = webwrite_retry(target_url, data, options, ...
            max_retries);
    end
    
    fclose('all');
    exit(0);
end

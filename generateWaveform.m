function txWaveform = generateWaveform(args)
    vhtCfg = wlanVHTConfig;             % Create packet configuration
    vhtCfg.ChannelBandwidth = args.ChannelBandwidth;
    vhtCfg.NumTransmitAntennas = args.NumTransmitAntennas;
    vhtCfg.NumSpaceTimeStreams = args.NumSpaceTimeStreams;
    vhtCfg.MCS = args.MCS;
    msdu = args.MSDU;

    idleTime = args.idleTime;
    oversamplingFactor = args.oversamplingFactor;

    % Initialize the scrambler with a random integer for each packet
    scramblerInitialization = randi([1 127]);

    % Create frame configuration
    macCfg = wlanMACFrameConfig('FrameType', 'QoS Data');
    macCfg.FrameFormat = args.FrameFormat;
    macCfg.MSDUAggregation = true;  % Form A-MSDUs internally
    data = [];
    

    % Generate PSDU bits containing A-MPDU with EOF delimiters and padding
    [psdu, apepLength] = wlanMACFrame(msdu, macCfg, vhtCfg, 'OutputFormat', 'bits');
    
    % Set the APEP length in the VHT configuration
    vhtCfg.APEPLength = apepLength;
    
    % Concatenate packet PSDUs for waveform generation
    data = [data; psdu]; %#ok<AGROW>

    % Generate baseband VHT packets
    txWaveform = wlanWaveformGenerator(data,vhtCfg, ...
        'NumPackets',1,'IdleTime',idleTime, ...
        'ScramblerInitialization',scramblerInitialization, ...
        'OversamplingFactor',oversamplingFactor);

    postProcFunc = str2func(args.postProcFunc);
    txWaveform = postProcFunc(txWaveform, args);
end


function alpha = getPathloss(distance, PLExponent, centerFrequency)
    %applyPathloss Returns the path loss factor in linear scale after
    %modeling the Bluetooth path loss
    %
    %   ALPHA = getPathloss(OBJ, DISTANCE, CENTERFREQUENCY) returns
    %   the path loss factor in linear scale
    %
    %   ALPHA returns the attenuation factor in linear scale to be
    %   applied on the received waveform.
    %
    %   DISTANCE is the distance between transmitter and receiver in
    %   meters.
    %
    %   CENTERFREQUENCY is an integer represents the center frequency
    %   in Hz.
    
    lamda = 3e8/centerFrequency;
    pathLoss = (distance^PLExponent)*(4*pi/lamda)^2;
    pathLossdB = 10*log10(pathLoss); % in dB
    alpha = 10^(-pathLossdB/20);
end

SELECT
    CONVERT_TIMEZONE(
        'UTC',
        'America/New_York',
        block_timestamp :: timestamp_ntz
    ) AS "Datetime",
    tx_id AS "tx_id",
    event_data ['id'] AS pack_id,
    event_data ['nfts'] AS nfts
FROM
    flow.core.fact_events
WHERE
    event_type = 'Revealed'
    AND event_contract = 'A.e4cf4bdc1751c65d.PackNFT'
    AND tx_succeeded = 'TRUE'
    AND block_timestamp :: DATE = {{ date }}

SELECT
    CONVERT_TIMEZONE(
        'UTC',
        'America/New_York',
        block_timestamp :: timestamp_ntz
    ) AS "Datetime",
    tx_id AS "tx_id",
    price AS "Price",
    buyer AS "Buyer",
    nft_id
FROM
    flow.core.ez_nft_sales
WHERE
    nft_collection = 'A.e4cf4bdc1751c65d.PackNFT'
    AND tx_succeeded = 'TRUE'
    AND block_timestamp :: DATE = {{ date }}

------------
UNSTRUCTURED(HI-RES):
------------

folder: cdp
         cdp_etiquette.pdf parsing took: 2.10s
folder: scanned-tables
         POZIBILAN 2022.pdf parsing took: 78.72s
         Banco Popilar Number 2.pdf parsing took: 94.44s
folder: native
         00b03d60-fe45-4318-a511-18ee921b7bbb.pdf parsing took: 3.25s
         0b0ab5f4-b654-4846-bd9b-18b3c1075c52.pdf parsing took: 39.75s
         0adb1fd6-d009-4097-bcf6-b8f3af38d3f0.pdf parsing took: 25.02s
folder: scanned
         machine.pdf parsing took: 54.29s
         medical.pdf parsing took: 76.11s
         les_americains.pdf parsing took: 643.84s
         agency.pdf parsing took: 114.19s
         clark.pdf parsing took: 27.89s
         tables_ocr.pdf parsing took: 81.21s
folder: rich
         language_learning.pdf parsing took: 2.60s
         dites nous tout....pdf parsing took: 1.62s

------------
UNSTRUCTURED(FAST):
------------
folder: cdp
         cdp_etiquette.pdf parsing took: 0.05s
folder: scanned-tables
        POZIBILAN 2022.pdf:  can't parse
        Banco Popilar Number 2.pdf:  can't parse
folder: native
         00b03d60-fe45-4318-a511-18ee921b7bbb.pdf parsing took: 0.07s
         0b0ab5f4-b654-4846-bd9b-18b3c1075c52.pdf parsing took: 0.86s
         0adb1fd6-d009-4097-bcf6-b8f3af38d3f0.pdf parsing took: 0.24s
folder: scanned
        machine.pdf parsing took: 0.02s
        medical.pdf parsing took: 0.04s
        les_americains.pdf parsing took: 5.90s
        agency.pdf:  can't parse
        clark.pdf:  can't parse
        tables_ocr.pdf:  can't parse
folder: rich
        language_learning.pdf:  can't parse
         dites nous tout....pdf parsing took: 0.02s

------------
Megaparse (
        strategy = AUTO
        Config = {
                provider=COREML,
                det_arch: str = "fast_base"
                det_batch_size: int = 2
                assume_straight_pages: bool = True
                preserve_aspect_ratio: bool = True
                symmetric_pad: bool = True
                load_in_8_bit: bool = False
                reco_arch: str = "crnn_vgg16_bn"
                rec_batch_size: int = 512
        }
)
------------
folder: cdp
        cdp_etiquette.pdf parsing took: 1.71s
folder: scanned-tables
        POZIBILAN 2022.pdf parsing took: 17.76s
        Banco Popilar Number 2.pdf parsing took: 19.25s
folder: native
        00b03d60-fe45-4318-a511-18ee921b7bbb.pdf parsing took: 0.96s
        0b0ab5f4-b654-4846-bd9b-18b3c1075c52.pdf parsing took: 12.57s
        0adb1fd6-d009-4097-bcf6-b8f3af38d3f0.pdf parsing took: 1.53s
folder: scanned
        machine.pdf parsing took: 9.90s
        medical.pdf parsing took: 13.09s
        les_americains.pdf parsing took: 139.53s
        agency.pdf parsing took: 10.73s
        clark.pdf parsing took: 10.69s
        tables_ocr.pdf parsing took: 15.58s
folder: rich
        language_learning.pdf parsing took: 1.74s
        dites nous tout....pdf parsing took: 0.64s
----
| Type            | PDF Name                          | Unstructured(HI-RES) | Unstructured(FAST)    | Megaparse( w/ doctr COREML)  |
|------------------|-----------------------------------|---------------------|----------------------|--------------------|
| **cdp**         | cdp_etiquette.pdf                 | 2.10s               | 0.05s (bad parsing)              | 1.71s             |
| **scanned-tables** | POZIBILAN 2022.pdf             | 78.72s              | can't parse          | 17.76s            |
| **scanned-tables** | Banco Popilar Number 2.pdf     | 94.44s              | can't parse          | 19.25s            |
| **native**       | 00b03d60-fe45-4318-a511-18ee921b7bbb.pdf | 3.25s  | 0.07s               | 0.96s             |
| **native**       | 0b0ab5f4-b654-4846-bd9b-18b3c1075c52.pdf | 39.75s | 0.86s               | 12.57s            |
| **native**       | 0adb1fd6-d009-4097-bcf6-b8f3af38d3f0.pdf | 25.02s | 0.24s               | 1.53s             |
| **scanned**      | machine.pdf                      | 54.29s              | 0.02s               | 9.90s             |
| **scanned**      | medical.pdf                      | 76.11s              | 0.04s               | 13.09s            |
| **scanned**      | les_americains.pdf               | 643.84s             | 5.90s               | 139.53s           |
| **scanned**      | agency.pdf                       | 114.19s             | can't parse          | 10.73s            |
| **scanned**      | clark.pdf                        | 28.89s              | can't parse          | 10.69s            |
| **scanned**      | tables_ocr.pdf                   | 81.21s              | can't parse          | 15.58s            |
| **rich**         | language_learning.pdf            | 2.60s               | can't parse          | 1.74s             |
| **rich**         | dites nous tout....pdf           | 1.62s               | 0.02s               | 0.64s             |

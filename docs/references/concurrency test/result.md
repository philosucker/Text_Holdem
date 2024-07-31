디스크 I/O 바운드 작업
test1
    Sync time: 43.93 seconds
    AsyncIO time: 77.73 seconds
    Multiprocessing time: 7.14 seconds
    AsyncIO with multiprocessing time: 18.40 seconds

    Sync time: 26.88 seconds
    AsyncIO time: 89.78 seconds
    Multiprocessing time: 6.60 seconds
    AsyncIO with multiprocessing time: 20.10 seconds

test2
    Sync time: 38.57 seconds
    AsyncIO time: 1499.45 seconds
    Multiprocessing time: 5.54 seconds
    AsyncIO with multiprocessing time: 5.96 seconds

harder test
    Sync time: 104.03 seconds
    AsyncIO time: 522.78 seconds generate_files(5000, 1000, 10) 절반으로 줄였는데도 멀티프로세싱보다 느리다
    Multiprocessing time: 27.38 seconds 
    AsyncIO with multiprocessing time: 348.51 seconds

    Sync time: 101.86 seconds
    AsyncIO time: 672.01 seconds
    Multiprocessing time: 27.13 seconds
    AsyncIO with multiprocessing time: 393.95 seconds

비동기 효과 없음. 오히려 동기보다 더 느림.
대규모 디스크I/O 작업에서는 멀티프로세싱이 압도적
소규모에서는 멀티프로세싱+비동기도 멀티프로세싱과 비슷하나 소폭 느림

CPU 바운드 작업 
    Sync time: 20.49 seconds
    AsyncIO time: 49.33 seconds
    Multiprocessing time: 5.24 seconds
    AsyncIO with multiprocessing time: 5.47 seconds

    Sync time: 21.88 seconds
    AsyncIO time: 57.88 seconds
    Multiprocessing time: 5.15 seconds
    AsyncIO with multiprocessing time: 5.51 seconds


멀티프로세싱이 최선.
멀티프로세싱+비동기는 소폭 느림

CPU 바운드 + 디스크 I/O 바운드 작업
    Sync time: 37.10 seconds
    AsyncIO time: 226.81 seconds
    Multiprocessing time: 9.56 seconds
    AsyncIO with multiprocessing time: 10.11 seconds

    Sync time: 37.66 seconds
    AsyncIO time: 251.74 seconds
    Multiprocessing time: 10.51 seconds
    AsyncIO with multiprocessing time: 10.76 seconds

harder
    Sync time: 215.37 seconds
    AsyncIO time: 759.75 seconds
    Multiprocessing time: 50.79 seconds
    AsyncIO with multiprocessing time: 53.56 seconds
멀티프로세싱이 최선
멀티프로세싱+비동기는 소폭 느림
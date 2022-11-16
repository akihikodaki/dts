; SPDX-License-Identifier: BSD-3-Clause
; Copyright(c) 2022 Intel Corporation

;
; Pipeline packet mirroring.
;
mirroring slots 4 sessions 64

;
; Pipeline input ports.
;
; Note: Customize the parameters below to match your setup.
;
port in 0 ethdev 0000:00:04.0 rxq 0 bsz 1
port in 1 ethdev 0000:00:05.0 rxq 0 bsz 1
port in 2 ethdev 0000:00:06.0 rxq 0 bsz 1
port in 3 ethdev 0000:00:07.0 rxq 0 bsz 1

;
; Pipeline output ports.
;
; Note: Customize the parameters below to match your setup.
;
port out 0 ethdev 0000:00:04.0 txq 0 bsz 1
port out 1 ethdev 0000:00:05.0 txq 0 bsz 1
port out 2 ethdev 0000:00:06.0 txq 0 bsz 1
port out 3 ethdev 0000:00:07.0 txq 0 bsz 1

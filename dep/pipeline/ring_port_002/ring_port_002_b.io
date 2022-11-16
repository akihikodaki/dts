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
port in 0 ring RING0 bsz 1
;
; Pipeline output ports.
;
; Note: Customize the parameters below to match your setup.
;
port out 0 ethdev 0000:00:04.0 txq 0 bsz 1

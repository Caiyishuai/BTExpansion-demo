(define (problem corridor-6-rooms)
  (:domain static-prune)

  ;; 6 个房间排成一条走廊： r1 - r2 - r3 - r4 - r5 - r6
  ;; 不做静态剪枝时 move 有 6x6 = 36 个实例；
  ;; 实际只有 10 条边（双向 5 段），其余 26 个实例永远不可执行。
  (:objects
    r1 r2 r3 r4 r5 r6 - location
    box - item
  )

  (:init
    (robot-at r1)
    (item-at box r6)
    (hand-empty)

    (connected r1 r2) (connected r2 r1)
    (connected r2 r3) (connected r3 r2)
    (connected r3 r4) (connected r4 r3)
    (connected r4 r5) (connected r5 r4)
    (connected r5 r6) (connected r6 r5)
  )

  (:goal (and (item-at box r1) (hand-empty)))
)

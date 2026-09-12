(define (problem unsupported-1)
  (:domain unsupported-showcase)

  (:objects
    room-a room-b - location
    vase - item
  )

  (:init
    (at room-a)
    (clear room-a)
    (fragile vase)
  )

  (:goal (or (holding vase) (and (at room-b) (clear room-b))))
)

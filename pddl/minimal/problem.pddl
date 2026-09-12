(define (problem p1)
  (:domain pick-and-place)

  (:objects
    cup - item
    kitchen desk - location
  )

  (:init (robot-at kitchen) (item-at cup kitchen) (hand-empty))

  ;; 把杯子从厨房搬到书桌
  (:goal (and (item-at cup desk)))
)

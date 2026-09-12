(define (problem fetch-cup-to-desk)
  (:domain robot-fetch)

  (:objects
    kitchen desk bar - location
    cup - item
  )

  (:init
    (robot-at bar)
    (item-at cup kitchen)
    (hand-empty)
    (reachable kitchen)
    (reachable desk)
    (reachable bar)
  )

  (:goal (and (item-at cup desk) (hand-empty)))
)

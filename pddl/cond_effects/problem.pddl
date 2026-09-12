(define (problem pick-vase-safely)
  (:domain conditional-pick)

  (:objects vase - item)

  (:init
    (on-table vase)
    (fragile vase)
    (heavy vase)
  )

  ;; 要拿到花瓶、且不能摔坏、且不能累
  ;; => 必须先 reinforce + lighten，再 pick
  (:goal (and (holding vase) (not (broken vase)) (not (tired))))
)

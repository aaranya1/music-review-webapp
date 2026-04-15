import React, { useState } from 'react';

function StarPicker({ value, onChange }) {
    const [hovered, setHovered] = useState(null)

    return (
        <div className='star-picker'>
            {[1, 2, 3, 4, 5].map(star => {
                const active = hovered !== null ? hovered : value
                const full = active >= star
                const half = !full && active >= star - 0.5
                return (
                    <span
                        key={star}
                        className='star-picker__star'
                        onMouseMove={(e) => {
                            const rect = e.currentTarget.getBoundingClientRect()
                            const isLeft = e.clientX - rect.left < rect.width / 2
                            setHovered(isLeft ? star - 0.5 : star)
                        }}
                        onMouseLeave={() => setHovered(null)}
                        onClick={(e) => {
                            const rect = e.currentTarget.getBoundingClientRect()
                            const isLeft = e.clientX - rect.left < rect.width / 2
                            onChange(isLeft ? star - 0.5 : star)
                        }}
                    >
                        <span className={`star-picker__fill ${full ? 'full' : half ? 'half' : 'empty'}`}>★</span>
                    </span>
                )
            })}
            {value > 0 && <span className='star-picker__value'>{value.toFixed(1)}</span>}
        </div>
    )
}

export default StarPicker


const EyeTestLabel = () => {
return (
<div className="grid grid-cols-[80px_repeat(4,1fr)] gap-2">
<label title=""></label>
<label title="Spherical">SPH</label>
<label title="Cylinder">CYL</label>
<label title="Axis">AXIS</label>
<label title="Addition">ADD</label>
</div>
)
}

const EyeTestLabelProps = () => {
 return (
    <div className="grid grid-cols-[80px_repeat(4,1fr)] md:grid-cols-5 gap-2">
    <label title="" className="block md:hidden"></label>
    <label title="Pupillary Distance">PD</label>
    <label title="Segment Height">SG</label>
    <label title="Vertical Distance">VD</label>
    <label title="Visual Acuity">VA</label>
  </div>
 )
    
}

export {EyeTestLabel,EyeTestLabelProps}



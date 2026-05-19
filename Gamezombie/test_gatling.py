import pygame, array, random, math, time
pygame.init()
try:
    pygame.mixer.init()
except Exception as e:
    print('mixer init failed:', e)

def gen_gatling():
    sample_rate=22050; duration=0.08; freq=110; noise_mix=0.7; volume_factor=22000
    n=int(sample_rate*duration); buf=array.array('h',[0]*n)
    for i in range(n):
        t=i/sample_rate; noise=random.uniform(-1,1)
        wave=math.sin(2*math.pi*freq*t)
        wave=0.5 if wave>0 else -0.5
        amp=math.exp(-6*(t/duration))
        val=int((wave*(1-noise_mix)+noise*noise_mix)*amp*volume_factor)
        buf[i]=max(-32768,min(32767,val))
    return pygame.mixer.Sound(buffer=buf)

s=gen_gatling()
s.set_volume(0.8)
print('Playing synthesized gatling sound...')
s.play()
time.sleep(0.7)
print('Done')

"""R11/R22: recompute exact McNemar (binomial), Fisher, risk differences, Newcombe CIs from macro counts. Pure stdlib."""
from math import comb, sqrt
def mcn(b,c,two=True):
    n=b+c; k=min(b,c)
    p1=sum(comb(n,i) for i in range(0,k+1))/2**n
    return min(1.0,2*p1) if two else p1
def mcn_one_greater(b,c):  # H_a: b>c ; P(X>=b | n, 0.5)
    n=b+c; return sum(comb(n,i) for i in range(b,n+1))/2**n
def fisher(a,b,c,d):
    n=a+b+c+d; r1=a+b; c1=a+c
    def p(x): return comb(r1,x)*comb(n-r1,c1-x)/comb(n,c1)
    p0=p(a); lo=max(0,c1-(n-r1)); hi=min(r1,c1)
    return sum(p(x) for x in range(lo,hi+1) if p(x)<=p0*(1+1e-9))
def wilson(k,n,z=1.959964):
    p=k/n; den=1+z*z/n; ctr=(p+z*z/(2*n))/den; h=z*sqrt(p*(1-p)/n+z*z/(4*n*n))/den; return ctr-h,ctr+h
def newcombe(k1,n1,k2,n2):
    p1,p2=k1/n1,k2/n2; l1,u1=wilson(k1,n1); l2,u2=wilson(k2,n2); d=p1-p2
    return d, d-sqrt((p1-l1)**2+(u2-p2)**2), d+sqrt((u1-p1)**2+(p2-l2)**2)
print("== R11 obscure suite (generated_obscure_stats.tex)")
for name,b,c,rep in [("primary Unl vs Flat",5,3,"0.726562"),("Full vs Unl",11,0,"<0.001"),("Full vs Flat",13,0,"<0.001"),
                     ("Unl vs Direct",8,0,"0.007812"),("Flat vs Direct",6,0,"0.031250"),("J1 primary",10,3,"0.092285"),("J2 primary",3,4,"1.0"),
                     ("subset empty",3,3,"1.0"),("subset overruler",2,3,"1.0"),("subset explicit",3,2,"1.0")]:
    print(f"{name}: b={b} c={c} two-sided exact p={mcn(b,c):.6f} (reported {rep})")
for name,kf,ko,rep_rd,rep_ci,rep_p in [("Direct",15,0,"+79.0%","[+53.9,+91.5]","2.46e-9"),("Flat",10,6,"+32.6%","[+5.5,+55.2]","0.028"),
                                       ("Unlabeled",15,8,"+52.3%","[+23.8,+70.0]","4.68e-4"),("Full",14,19,"+10.3%","[-16.6,+33.3]","0.541")]:
    d,lo,hi=newcombe(kf,19,ko,30); p=fisher(kf,19-kf,ko,30-ko)
    print(f"cross {name}: famous {kf}/19={kf/19:.4f} obscure {ko}/30={ko/30:.4f} RD={d*100:+.2f}% (rep {rep_rd}) Newcombe=[{lo*100:+.1f},{hi*100:+.1f}] (rep {rep_ci}) Fisher p={p:.3g} (rep {rep_p})")
print("\n== R22 temporal probe (generated_stats.tex)")
print("H1 SPTLR b=0 c=3: one-sided(b>c) p=",mcn_one_greater(0,3)," two-sided=",mcn(0,3))
print("H1 HLCR b=20 c=1 two-sided p=",mcn(20,1))
for name,bb,cc,rep in [("H2",(11,16),(5,6),"[0.0133,0.1662]"),("H3",(10,13),(4,8),"[0.0245,0.4073]"),("H4",(8,11),(2,6),"[0.0112,0.3953]")]:
    pmin_one=mcn(bb[1],cc[0],False); pmax_one=mcn(bb[0],cc[1],False)
    pmin_two=mcn(bb[1],cc[0]); pmax_two=mcn(bb[0],cc[1])
    print(f"{name}: one-sided range [{pmin_one:.4f},{pmax_one:.4f}]; two-sided range [{pmin_two:.4f},{pmax_two:.4f}] (reported {rep})")
for name,b,c in [("H2 cc",2,4),("H3 cc",5,1),("H4 cc",1,1)]:
    print(f"{name}: b={b} c={c} two-sided p={mcn(b,c):.4f}; direction {'TERRA better' if b>c else ('tie' if b==c else 'TERRA worse')}")
# kappa paradox check: GPT-OSS 289/315 Level 0
print("GPT-OSS Level0 share 289/315 =",289/315)
print("HLCR ratio 76/38 =",76/38)

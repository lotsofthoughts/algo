package main

import (
  "container/heap"
  "encoding/json"
  "errors"
  "flag"
  "fmt"
  "path/filepath"
  "io"
  "os"
  "sort"
)

type AnyMap map[string]any
func readJSON(path string) (AnyMap, error) { var b []byte; var err error; if path=="" { b,err=io.ReadAll(os.Stdin) } else { b,err=os.ReadFile(path); if err!=nil { b,err=os.ReadFile(filepath.Join("..", path)) } }; if err!=nil {return nil,err}; var m AnyMap; return m, json.Unmarshal(b,&m) }
func ints(v any) []int { xs:=v.([]any); out:=make([]int,len(xs)); for i,x:=range xs { out[i]=int(x.(float64)) }; return out }
func matrixInt(v any) [][]int { rows:=v.([]any); out:=make([][]int,len(rows)); for i,r:=range rows { out[i]=ints(r) }; return out }
func matrixStr(v any) [][]string { rows:=v.([]any); out:=make([][]string,len(rows)); for i,r:=range rows { arr:=r.([]any); out[i]=make([]string,len(arr)); for j,x:=range arr { out[i][j]=x.(string)} }; return out }
func edges2(v any) [][]int { return matrixInt(v) }
func edges3(v any) [][]int { return matrixInt(v) }

func lc200(d AnyMap) any { g:=matrixStr(d["grid"]); R,C:=len(g),len(g[0]); seen:=map[[2]int]bool{}; var dfs func(int,int); dfs=func(r,c int){ if r<0||c<0||r>=R||c>=C||g[r][c]!="1"||seen[[2]int{r,c}] {return}; seen[[2]int{r,c}]=true; dfs(r+1,c); dfs(r-1,c); dfs(r,c+1); dfs(r,c-1)}; count:=0; for r:=0;r<R;r++{for c:=0;c<C;c++{if g[r][c]=="1"&&!seen[[2]int{r,c}]{count++; dfs(r,c)}}}; return count }
func lc994(d AnyMap) any { g:=matrixInt(d["grid"]); R,C:=len(g),len(g[0]); type cell struct{r,c,t int}; q:=[]cell{}; fresh:=0; for r:=0;r<R;r++{for c:=0;c<C;c++{if g[r][c]==2{q=append(q,cell{r,c,0})} else if g[r][c]==1{fresh++}}}; min:=0; dirs:=[][2]int{{1,0},{-1,0},{0,1},{0,-1}}; for len(q)>0{x:=q[0]; q=q[1:]; min=x.t; for _,di:=range dirs{nr,nc:=x.r+di[0],x.c+di[1]; if nr>=0&&nc>=0&&nr<R&&nc<C&&g[nr][nc]==1{g[nr][nc]=2; fresh--; q=append(q,cell{nr,nc,x.t+1})}}}; if fresh>0{return -1}; return min }
func lc33(d AnyMap) any { nums:=ints(d["nums"]); target:=int(d["target"].(float64)); lo,hi:=0,len(nums)-1; for lo<=hi{mid:=(lo+hi)/2; if nums[mid]==target{return mid}; if nums[lo]<=nums[mid]{if nums[lo]<=target&&target<nums[mid]{hi=mid-1}else{lo=mid+1}}else{if nums[mid]<target&&target<=nums[hi]{lo=mid+1}else{hi=mid-1}}}; return -1 }
func lc3(d AnyMap) any { s:=d["s"].(string); seen:=map[byte]int{}; left,best:=0,0; for right:=0; right<len(s); right++{ch:=s[right]; if p,ok:=seen[ch]; ok&&p>=left{left=p+1}; seen[ch]=right; if right-left+1>best{best=right-left+1}}; return best }
func lc210(d AnyMap) any { n:=int(d["numCourses"].(float64)); prereq:=edges2(d["prerequisites"]); graph:=make([][]int,n); indeg:=make([]int,n); for _,e:=range prereq{course,pre:=e[0],e[1]; graph[pre]=append(graph[pre],course); indeg[course]++}; q:=[]int{}; for i,x:=range indeg{if x==0{q=append(q,i)}}; order:=[]int{}; for len(q)>0{x:=q[0];q=q[1:]; order=append(order,x); for _,nxt:=range graph[x]{indeg[nxt]--; if indeg[nxt]==0{q=append(q,nxt)}}}; if len(order)!=n{return []int{}}; return order }
type dsu struct{p,r map[int]int}; func newDSU()*dsu{return &dsu{map[int]int{},map[int]int{}}}; func (d *dsu)find(x int)int{ if _,ok:=d.p[x];!ok{d.p[x]=x}; if d.p[x]!=x{d.p[x]=d.find(d.p[x])}; return d.p[x]}; func (d *dsu)union(a,b int)bool{ra,rb:=d.find(a),d.find(b); if ra==rb{return false}; if d.r[ra]<d.r[rb]{ra,rb=rb,ra}; d.p[rb]=ra; if d.r[ra]==d.r[rb]{d.r[ra]++}; return true}
func lc684(d AnyMap) any { uf:=newDSU(); for _,e:=range edges2(d["edges"]){ if !uf.union(e[0],e[1]){return e} }; return []int{} }
type pair struct{d,n int}; type pq []pair; func (p pq)Len()int{return len(p)}; func (p pq)Less(i,j int)bool{return p[i].d<p[j].d}; func (p pq)Swap(i,j int){p[i],p[j]=p[j],p[i]}; func (p *pq)Push(x any){*p=append(*p,x.(pair))}; func (p *pq)Pop()any{old:=*p; x:=old[len(old)-1]; *p=old[:len(old)-1]; return x}
func lc743(d AnyMap) any { times:=edges3(d["times"]); n:=int(d["n"].(float64)); k:=int(d["k"].(float64)); graph:=map[int][]pair{}; for _,e:=range times{graph[e[0]]=append(graph[e[0]],pair{e[2],e[1]})}; dist:=map[int]int{}; h:=&pq{{0,k}}; heap.Init(h); for h.Len()>0{x:=heap.Pop(h).(pair); if _,ok:=dist[x.n];ok{continue}; dist[x.n]=x.d; for _,nx:=range graph[x.n]{ if _,ok:=dist[nx.n];!ok{heap.Push(h,pair{x.d+nx.d,nx.n})} } }; if len(dist)!=n{return -1}; mx:=0; for _,v:=range dist{if v>mx{mx=v}}; return mx }
func lc347(d AnyMap) any { nums:=ints(d["nums"]); k:=int(d["k"].(float64)); cnt:=map[int]int{}; for _,n:=range nums{cnt[n]++}; keys:=[]int{}; for k:=range cnt{keys=append(keys,k)}; sort.Slice(keys,func(i,j int)bool{return cnt[keys[i]]>cnt[keys[j]]}); return keys[:k] }
func lc79(d AnyMap) any { b:=matrixStr(d["board"]); word:=d["word"].(string); R,C:=len(b),len(b[0]); var dfs func(int,int,int)bool; dfs=func(r,c,i int)bool{if i==len(word){return true}; if r<0||c<0||r>=R||c>=C||b[r][c]!=string(word[i]){return false}; tmp:=b[r][c]; b[r][c]="#"; ok:=dfs(r+1,c,i+1)||dfs(r-1,c,i+1)||dfs(r,c+1,i+1)||dfs(r,c-1,i+1); b[r][c]=tmp; return ok}; for r:=0;r<R;r++{for c:=0;c<C;c++{if dfs(r,c,0){return true}}}; return false }
func lc322(d AnyMap) any { coins:=ints(d["coins"]); amount:=int(d["amount"].(float64)); inf:=amount+1; dp:=make([]int,amount+1); for i:=1;i<=amount;i++{dp[i]=inf}; for a:=1;a<=amount;a++{for _,coin:=range coins{if a-coin>=0&&dp[a-coin]+1<dp[a]{dp[a]=dp[a-coin]+1}}}; if dp[amount]==inf{return -1}; return dp[amount] }
var solvers=map[string]func(AnyMap)any{"leetcode-200":lc200,"leetcode-994":lc994,"leetcode-33":lc33,"leetcode-3":lc3,"leetcode-210":lc210,"leetcode-684":lc684,"leetcode-743":lc743,"leetcode-347":lc347,"leetcode-79":lc79,"leetcode-322":lc322}
func solve(args []string) error { fs:=flag.NewFlagSet("solve",flag.ExitOnError); in:=fs.String("input","",""); fs.StringVar(in,"i","",""); // allow both: solve --input file target, and solve target --input file
  normalized:=[]string{}; target:=""; for i:=0;i<len(args);i++{ if args[i]=="--input"||args[i]=="-i"{ normalized=append(normalized,args[i]); if i+1<len(args){ normalized=append(normalized,args[i+1]); i++}; continue }; if target==""{ target=args[i] } else { normalized=append(normalized,args[i]) } }; fs.Parse(normalized); if target==""{ if fs.NArg()<1{return errors.New("target required")}; target=fs.Arg(0) }; data,err:=readJSON(*in); if err!=nil{return err}; out:=solvers[target](data); return json.NewEncoder(os.Stdout).Encode(out) }
func main(){ if len(os.Args)<2{fmt.Fprintln(os.Stderr,"usage: algo solve <target> [--input file]"); os.Exit(2)}; var err error; switch os.Args[1]{case "solve": err=solve(os.Args[2:]); default: err=fmt.Errorf("unsupported command in Go v1: %s", os.Args[1])}; if err!=nil{fmt.Fprintln(os.Stderr,err); os.Exit(1)} }
